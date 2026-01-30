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


class Trading212Reader(Reader):

    def read(self, input_file: Path) -> Trading212Report:
        report = Trading212Report()

        with input_file.open("r") as csvfile:
            reader = DictReader(csvfile)

            for row in reader:
                action = row.get("Action", "")
                stock = Trading212Stock.from_dict(row)

                if action == T212Action.MB or action == T212Action.LB:
                    report.buys.append(stock)

                elif action == T212Action.MS or action == T212Action.LS:
                    report.sells.append(stock)

                elif action == T212Action.DIV:
                    report.dividends.append(
                        Dividend(
                            ticker=stock.ticker,
                            time=stock.time,
                            amount=stock.total_price,
                        )
                    )

                elif action == T212Action.DEP:
                    report.deposit += stock.total_price

        return report
