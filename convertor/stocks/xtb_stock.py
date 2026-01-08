from datetime import datetime
from typing import Self

from convertor.currency import Currency
from .stock import Stock


class XtbStock(Stock):

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        quantity, share_price = (
            data.get("Comment", "")
            .removeprefix("OPEN BUY")
            .removeprefix("CLOSE BUY")
            .replace("@", "")
            .split()
        )
        if "/" in quantity:
            quantity = quantity.split("/")[0]

        return cls(
            ticker=data.get("Symbol"),
            time=datetime.strptime(data.get("Time"), "%d.%m.%Y %H:%M:%S").strftime("%Y%m%d"),
            quantity=float(quantity),
            share_price=float(share_price),
            currency_main=Currency("EUR"),
            total_price=float(number) if (number := data.get("Amount")) else -1.0,
        )
