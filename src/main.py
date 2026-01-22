#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path

from convertor.readers.reader import Reader
from convertor.readers.trading212_reader import Trading212Reader
from convertor.readers.xtb_reader import XtbReader
from convertor.constants import YAHOO_EXPORT
from convertor.store import Store


class ValidatePathsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None) -> None:
        if not values:
            return

        for path in values:
            if not isinstance(path, Path):
                parser.error(f"Error occured with path: '{path}'")
            if not path.exists():
                parser.error(f"The path '{path}' does not exist")
            if not path.is_file():
                parser.error(f"The path '{path}' is not a file")
                # check file suffix (xlsx or csv)

        setattr(namespace, self.dest, values)


def arg_parser_init() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Portfolio convertor")
    parser.add_argument(
        "inputs", nargs="+", type=Path, action=ValidatePathsAction, help="Input files"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="./output", help="Output file"
    )
    parser.add_argument(
        "--yahoo",
        help="Yahoo finance input format, output file is csv",
        action="store_true",
    )
    return parser.parse_args()


def yahoo_output(output_file: str, store: Store) -> None:
    with open(output_file, "w+") as file:
        writer = csv.DictWriter(file, YAHOO_EXPORT.to_list())
        writer.writeheader()
        writer.writerows([stock.to_yahoo() for stock in store.buys])
        writer.writerows([stock.to_yahoo() for stock in store.sells])


def get_broker(input_file: Path) -> Reader:
    match input_file.suffix:
        case ".csv":
            return Trading212Reader()
        case ".xlsx":
            return XtbReader()

    raise ValueError(f"Not supported file extension: {input_file.suffix}")


def main() -> None:
    args = arg_parser_init()

    store = Store()
    for input_file in args.inputs:
        reader = get_broker(input_file)
        buys, sells, deposits = reader.read(input_file)
        store.buys.extend(buys)
        store.sells.extend(sells)
        store.deposits += deposits

    if args.yahoo:
        yahoo_output(args.output, store)
        return

    with open(args.output, "w") as output_file:
        json.dump(
            {
                "buys": store.dump_buys_to_json(),
                "sells": store.dump_sells_to_json(),
                "deposits": store.deposits,
            },
            output_file,
            indent=4,
        )


if __name__ == "__main__":
    main()
