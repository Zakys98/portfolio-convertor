from csv import DictReader
from collections.abc import Sequence
from pathlib import Path

from .reader import Reader
from convertor.stocks.trading212_stock import Trading212Stock


class Trading212Reader(Reader):

    def read(self, input_file: Path) -> Sequence[Trading212Stock]:
        buys: list[Trading212Stock] = []
        sells: list[Trading212Stock] = []
        deposits: float = 0.0

        with input_file.open("r") as csvfile:
            reader = DictReader(csvfile)

            for row in reader:
                action = row.get("Action", "")
                stock = Trading212Stock.from_dict(row)

                if action == "Market buy" or action == "Limit buy":
                    buys.append(stock)

                elif action == "Market sell" or action == "Limit sell":
                    sells.append(stock)

                elif action == "Deposit":
                    deposits += stock.total_price
        return buys
