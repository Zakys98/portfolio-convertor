from pydantic import BaseModel, Field
from collections import defaultdict
from itertools import chain

from convertor.stocks.stock import Stock
from convertor.report import Report


class ReportManager[T: Stock](BaseModel):
    reports: list[Report[T]] = Field(default_factory=list)

    def _filter_by_time(self, stock):
        return stock["time"]

    def dump_buys_to_json(self) -> list[dict[str, str | float]]:
        return sorted(
            [stock.model_dump() for report in self.reports for stock in report.buys],
            key=self._filter_by_time,
        )

    def dump_sells_to_json(self)-> list[dict[str, str | float]]:
        return sorted(
            [stock.model_dump() for report in self.reports for stock in report.sells],
            key=self._filter_by_time,
        )

    def dump_dividends_to_json(self)-> list[dict[str, str | float]]:
        return sorted(
            [
                stock.model_dump()
                for report in self.reports
                for stock in report.dividends
            ],
            key=self._filter_by_time,
        )

    def dump_deposits_to_json(self) -> dict[str, float]:
        totals = defaultdict(float)

        for report in self.reports:
            currency_key = report.deposit_currency.value
            totals[currency_key] += report.deposit

        return dict(totals)

    def dump_to_yahoo(self)-> list[dict[str, str | float | int]]:
        return [
            stock.to_yahoo()
            for report in self.reports
            for stock in chain(report.buys, report.sells)
        ]
