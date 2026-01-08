from csv import DictReader

from .reader import Reader
from convertor.stocks.xtb_stock import XtbStock


class XtbReader(Reader[XtbStock]):

    def read(self, input_file: str) -> None:
        with open(input_file, "r") as csvfile:
            reader = DictReader(csvfile, delimiter=";")

            for row in reader:
                action = row.get("Type", "")

                if action == "Nákup akcií/ETF":
                    stock = XtbStock.from_dict(row)
                    self._buys.insert(0, stock)

                elif action == "Prodej akcií/ ETF":
                    stock = XtbStock.from_dict(row)
                    self._sells.insert(0, stock)

                elif action == "Vklad":
                    self._deposits += stock.total_price
