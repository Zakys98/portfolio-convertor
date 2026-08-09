import csv
import json
from collections import defaultdict
from itertools import chain
from pathlib import Path

from pydantic import BaseModel, Field

from convertor.constants import Standard
from convertor.report import Report
from convertor.stocks.stock import Stock


class ReportManager(BaseModel):
    reports: list[Report[Stock]] = Field(default_factory=list)

    def _filter_by_time(self, stock: dict[str, str | float]) -> str | float:
        return stock["time"]

    def _trades(self) -> list[tuple[str, Stock]]:
        """Every buy and sell tagged with its type, oldest first.

        Dividends are excluded: the importer derives them itself, and DIVIDEND
        is not a type it accepts.
        """
        trades: list[tuple[str, Stock]] = [
            *(("BUY", stock) for report in self.reports for stock in report.buys),
            *(("SELL", stock) for report in self.reports for stock in report.sells),
        ]
        trades.sort(key=lambda trade: trade[1].time)
        return trades

    def write_csv(self, output_file: Path) -> None:
        with output_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, Standard.to_list())
            writer.writeheader()
            writer.writerows(stock.to_standard(type_) for type_, stock in self._trades())

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
