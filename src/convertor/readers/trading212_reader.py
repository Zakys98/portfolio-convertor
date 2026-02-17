from csv import DictReader
from enum import StrEnum
from pathlib import Path

from convertor.readers.reader import Reader
from convertor.stocks.trading212_stock import Trading212Stock
from convertor.report import Trading212Report
from convertor.stocks.dividend import Dividend


class T212Action(StrEnum):
    DEP = "Deposit"
    DIV = "Dividend (Dividend)"
    MB = "Market buy"
    MS = "Market sell"
    LB = "Limit buy"
    LS = "Limit sell"


class Trading212Reader(Reader[Trading212Report]):
    BUY_ACTIONS = {T212Action.MB, T212Action.LB}
    SELL_ACTIONS = {T212Action.MS, T212Action.LS}

    def _parse_stock_transaction(self, row: dict[str, str]) -> Trading212Stock | None:
        """Parse stock transaction from CSV row."""
        try:
            return Trading212Stock.from_dict(row)
        except (ValueError, KeyError, TypeError):
            return None

    def _parse_dividend(self, row: dict[str, str]) -> Dividend | None:
        """Parse dividend transaction from CSV row."""
        try:
            stock = Trading212Stock.from_dict(row)
            if stock.ticker and stock.time:
                return Dividend(
                    ticker=stock.ticker,
                    time=stock.time,
                    amount=stock.total_price,
                )
        except (ValueError, KeyError, TypeError):
            pass
        return None

    def _parse_deposit(self, row: dict[str, str]) -> float:
        """Parse deposit transaction and return the amount."""
        try:
            stock = Trading212Stock.from_dict(row)
            if stock.total_price == -1.0:
                return 0.0
            return stock.total_price
        except (ValueError, KeyError, TypeError):
            return 0.0

    def read(self, input_file: Path) -> Trading212Report:
        report = Trading212Report()

        with input_file.open("r") as csvfile:
            reader = DictReader(csvfile)

            for row in reader:
                action_str = row.get("Action", "")

                if not action_str:
                    continue

                try:
                    action = T212Action(action_str)
                except ValueError:
                    continue

                # Handle buy transactions
                if action in self.BUY_ACTIONS:
                    if stock := self._parse_stock_transaction(row):
                        report.buys.append(stock)

                # Handle sell transactions
                elif action in self.SELL_ACTIONS:
                    if stock := self._parse_stock_transaction(row):
                        report.sells.append(stock)

                # Handle dividends
                elif action == T212Action.DIV:
                    if dividend := self._parse_dividend(row):
                        report.dividends.append(dividend)

                # Handle deposits
                elif action == T212Action.DEP:
                    report.deposit += self._parse_deposit(row)

        return report
