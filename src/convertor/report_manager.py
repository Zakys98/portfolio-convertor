import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from itertools import chain

from convertor.stocks.stock import Stock
from convertor.report import Report


class ReportManager(BaseModel):
    reports: list[Report[Stock]] = Field(default_factory=list)

    def _filter_by_time(self, stock: dict[str, str | float]) -> str | float:
        return stock["time"]

    def transactions(self) -> list[dict[str, Any]]:
        transactions: list[dict[str, Any]] = []

        for type_, items in (
            ("BUY", [s for r in self.reports for s in r.buys]),
            ("SELL", [s for r in self.reports for s in r.sells]),
            ("DIVIDEND", [s for r in self.reports for s in r.dividends]),
        ):
            for item in items:
                transactions.append({"type": type_} | item.model_dump())

        transactions.sort(key=self._filter_by_time)

        return transactions

    def write_csv(self, output_file: Path) -> None:
        transactions = self.transactions()
        fieldnames = list(dict.fromkeys(k for row in transactions for k in row))
        with output_file.open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(transactions)

    def write_json(self, output_file: Path) -> None:
        with output_file.open("w") as file:
            json.dump(self.transactions(), file, indent=4)

    def dump_to_yahoo(self)-> list[dict[str, str | float | int]]:
        return [
            stock.to_yahoo()
            for report in self.reports
            for stock in chain(report.buys, report.sells)
        ]
