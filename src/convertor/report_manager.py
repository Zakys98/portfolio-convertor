import csv
import json
from collections import defaultdict
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
        if not transactions:
            output_file.write_text("", encoding="utf-8")
            return
        fieldnames = list(dict.fromkeys(k for row in transactions for k in row))
        with output_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(transactions)

    def _deposits(self) -> dict[str, float]:
        totals: defaultdict[str, float] = defaultdict(float)
        for report in self.reports:
            totals[report.deposit_currency.value] += report.deposit
        return dict(totals)

    def write_json(self, output_file: Path) -> None:
        buys = sorted(
            [s.model_dump() for r in self.reports for s in r.buys],
            key=self._filter_by_time,
        )
        sells = sorted(
            [s.model_dump() for r in self.reports for s in r.sells],
            key=self._filter_by_time,
        )
        dividends = sorted(
            [s.model_dump() for r in self.reports for s in r.dividends],
            key=self._filter_by_time,
        )
        with output_file.open("w", encoding="utf-8") as file:
            json.dump(
                {"buys": buys, "sells": sells, "dividends": dividends, "deposits": self._deposits()},
                file,
                indent=4,
            )

    def dump_to_yahoo(self)-> list[dict[str, str | float | int]]:
        return [
            stock.to_yahoo()
            for report in self.reports
            for stock in chain(report.buys, report.sells)
        ]
