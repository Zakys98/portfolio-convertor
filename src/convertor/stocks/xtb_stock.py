from datetime import datetime
from typing import Self

from convertor.currency import Currency
from convertor.stocks.stock import Stock
from convertor.utils import date_to_string


class XtbStock(Stock):

    @classmethod
    def from_dict(cls, line: tuple[datetime, str, str, float | int], currency: Currency) -> Self:
        # Extract quantity string from the transaction description
        quantity_str = (
            line[1]
            .removeprefix("OPEN BUY")
            .removeprefix("CLOSE BUY")
            .replace("@", "")
            .split()[0]
        )
        if "/" in quantity_str:
            quantity_str = quantity_str.split("/")[0]

        quantity = float(quantity_str)
        total_price = abs(float(number)) if (number := line[3]) else -1.0
        share_price = round(total_price / quantity, 2)

        return cls(
            ticker=line[2],
            time=date_to_string(line[0]),
            quantity=quantity,
            share_price=share_price,
            currency_main=currency,
            total_price=total_price,
        )
