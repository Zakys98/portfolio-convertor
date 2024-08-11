#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
import json

from .readers.trading212_reader import Trading212Reader


def arg_parser_init() -> Namespace:
    parser = ArgumentParser("Portfolio convertor")
    parser.add_argument("-i", "--input", type=str, required=True, help="Input file")
    group = parser.add_argument_group("Input file type", "Choose type of input file")
    exclusive_group = group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument("--t212", help="trading212 input file", action="store_true")
    exclusive_group.add_argument("--xtb", help="xtb input file", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arg_parser_init()
    if args.t212:
        reader = Trading212Reader()
        reader.read(args.input)
    else:
        raise RuntimeError("Not supported yet")
    with open("./test.json", "w") as output_file:
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
