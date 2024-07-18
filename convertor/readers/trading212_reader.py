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
                if action == "Market buy":
                    self._buys.append(stock)
                    continue
                if action == "Market sell":
                    self._sells.append(stock)
                    continue
                if action == "Deposit":
                    self._deposits += stock.total_price
                    continue

    def dump_buys_to_json(self) -> list[dict[str, str | float]]:
        return [stock.model_dump() for stock in self._buys]

    def dump_sells_to_json(self) -> list[dict[str, str | float]]:
        return [stock.model_dump() for stock in self._sells]
