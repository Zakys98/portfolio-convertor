#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Sequence

from convertor.readers.reader import Reader
from convertor.readers.trading212_reader import Trading212Reader
from convertor.readers.xtb_reader import XtbReader
from convertor.constants import FileExtension, Yahoo
from convertor.report_manager import ReportManager


class ValidatePathsAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
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
        "-o", "--output", type=Path, default=Path("out.json"), help="Output file"
    )
    parser.add_argument(
        "--yahoo",
        help="Yahoo finance input format, output file is csv",
        action="store_true",
    )
    return parser.parse_args()


def yahoo_output(output_file: Path, manager: ReportManager) -> None:
    # Ensure output file has .csv extension for yahoo format
    if output_file.suffix.lower() != FileExtension.CSV:
        output_file = output_file.with_suffix(FileExtension.CSV)

    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(file, Yahoo.to_list())
        writer.writeheader()
        writer.writerows(manager.dump_to_yahoo())


def get_broker(input_file: Path) -> XtbReader | Trading212Reader:
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
        manager.reports.append(report)  # type: ignore[arg-type]

    if args.yahoo:
        yahoo_output(args.output, manager)
        return

    with args.output.open("w") as output_file:
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
