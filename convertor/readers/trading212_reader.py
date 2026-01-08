from csv import DictReader

from .reader import Reader
from convertor.stocks.trading212_stock import Trading212Stock


class Trading212Reader(Reader[Trading212Stock]):

    def read(self, input_file: str) -> None:
        with open(input_file, "r") as csvfile:
            reader = DictReader(csvfile)

            for row in reader:
                action = row.get("Action", "")
                stock = Trading212Stock.from_dict(row)

                if action == "Market buy" or action == "Limit buy":
                    self._buys.append(stock)

                elif action == "Market sell" or action == "Limit sell":
                    self._sells.append(stock)

                elif action == "Deposit":
                    self._deposits += stock.total_price
