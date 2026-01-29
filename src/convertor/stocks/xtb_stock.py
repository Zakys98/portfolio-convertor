from datetime import datetime
from typing import Self

from convertor.currency import Currency
from convertor.stocks.stock import Stock


class XtbStock(Stock):

    @classmethod
    def from_dict(cls, line: tuple[datetime, str, str, str], currency: Currency) -> Self:
        quantity, share_price = (
            line[1]
            .removeprefix("OPEN BUY")
            .removeprefix("CLOSE BUY")
            .replace("@", "")
            .split()
        )
        if "/" in quantity:
            quantity = quantity.split("/")[0]

        return cls(
            ticker=line[2],
            time=line[0].strftime("%Y%m%d"),
            quantity=float(quantity),
            share_price=float(share_price),
            currency_main=currency,
            total_price=abs(float(number)) if (number := line[3]) else -1.0,
        )
