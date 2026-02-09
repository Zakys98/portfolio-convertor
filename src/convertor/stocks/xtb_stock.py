from datetime import datetime
from typing import Self

from convertor.currency import Currency
from convertor.stocks.stock import Stock
from convertor.utils import date_to_string


class XtbStock(Stock):

    @classmethod
    def from_dict(cls, line: tuple[datetime, str, str, str], currency: Currency) -> Self:
        quantity = (
            line[1]
            .removeprefix("OPEN BUY")
            .removeprefix("CLOSE BUY")
            .replace("@", "")
            .split()[0]
        )
        if "/" in quantity:
            quantity = quantity.split("/")[0]
        quantity = float(quantity)
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
