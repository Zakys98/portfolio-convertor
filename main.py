#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
import csv
import json
import os.path

from convertor.readers.trading212_reader import Trading212Reader
from convertor.readers.xtb_reader import XtbReader
from convertor.constants import YAHOO_EXPORT


def arg_parser_init() -> Namespace:
    parser = ArgumentParser("Portfolio convertor")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input file")
    parser.add_argument("-o", "--output", type=str, default="./output.json", help="Output file")
    parser.add_argument(
        "--yahoo", help="Yahoo finance input format, output file is csv", action="store_true"
    )
    group = parser.add_argument_group(
        "Broker input file", "Select the broker for the input file"
    )
    exclusive_group = group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument("--t212", help="Trading212 input file", action="store_true")
    exclusive_group.add_argument("--xtb", help="XTB input file", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arg_parser_init()
    if args.t212:
        reader = Trading212Reader()
    elif args.xtb:
        reader = XtbReader()
    else:
        raise RuntimeError("Not supported yet")

    reader.read(args.input)

    if args.yahoo:
        previous_stocks = []

        if os.path.exists(args.output):
            with open(args.output, "r") as file:
                csv_reader = csv.DictReader(file, YAHOO_EXPORT.to_list())
                previous_stocks = [row for row in csv_reader][1:]

        with open(args.output, "w+") as file:
            writer = csv.DictWriter(file, YAHOO_EXPORT.to_list())
            writer.writeheader()
            if previous_stocks:
                writer.writerows(previous_stocks)
            writer.writerows([stock.to_yahoo() for stock in reader.buys])
            writer.writerows([stock.to_yahoo() for stock in reader.sells])

        return

    with open(args.output, "w") as output_file:
        json.dump(
            {
                "buys": reader.dump_buys_to_json(),
                "sells": reader.dump_sells_to_json(),
                "deposits": reader.deposits,
            },
            output_file,
            indent=4,
        )


if __name__ == "__main__":
    main()
