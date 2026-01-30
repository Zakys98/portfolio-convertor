#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path

from convertor.readers.reader import Reader
from convertor.readers.trading212_reader import Trading212Reader
from convertor.readers.xtb_reader import XtbReader
from convertor.constants import FileExtension, Yahoo
from convertor.report_manager import ReportManager


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
            if path.suffix.lower() not in [FileExtension.CSV, FileExtension.XLSX]:
                parser.error(f"Unsupported file extension: {path.suffix}")

        setattr(namespace, self.dest, values)


def arg_parser_init() -> argparse.Namespace:
    parser = argparse.ArgumentParser("Portfolio convertor")
    parser.add_argument(
        "inputs", nargs="+", type=Path, action=ValidatePathsAction, help="Input files"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="out.json", help="Output file"
    )
    parser.add_argument(
        "--yahoo",
        help="Yahoo finance input format, output file is csv",
        action="store_true",
    )
    return parser.parse_args()


def yahoo_output(output_file: str, manager: ReportManager) -> None:
    with open(output_file, "w", newline="") as file:
        writer = csv.DictWriter(file, Yahoo.to_list())
        writer.writeheader()
        writer.writerows(manager.dump_to_yahoo())


def get_broker(input_file: Path) -> Reader:
    match input_file.suffix:
        case FileExtension.CSV:
            return Trading212Reader()
        case FileExtension.XLSX:
            return XtbReader()

    raise ValueError(f"Not supported file extension: {input_file.suffix}")


def main() -> None:
    args = arg_parser_init()

    manager = ReportManager()
    for input_file in args.inputs:
        reader = get_broker(input_file)
        report = reader.read(input_file)
        manager.reports.append(report)

    if args.yahoo:
        yahoo_output(args.output, manager)
        return

    with open(args.output, "w") as output_file:
        json.dump(
            {
                "buys": manager.dump_buys_to_json(),
                "sells": manager.dump_sells_to_json(),
                "dividends": manager.dump_dividends_to_json(),
                "deposits": manager.dump_deposits_to_json(),
            },
            output_file,
            indent=4,
        )


if __name__ == "__main__":
    main()
