from datetime import datetime
from typing import Self

from convertor.currency import Currency
from .stock import Stock


class Trading212Stock(Stock):
    name: str
    currency_order: Currency
    exchange_rate: float

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            ticker=data.get("Ticker", ""),
            name=data.get("Name", ""),
            time=datetime.strptime(data.get("Time", "").split(" ")[0], "%Y-%m-%d").strftime("%Y%m%d"),
            quantity=float(number) if (number := data.get("No. of shares")) else -1.0,
            share_price=float(number) if (number := data.get("Price / share")) else -1.0,
            currency_main=(
                Currency(curr)
                if (curr := data.get("Currency (Price / share)"))
                else Currency("USD")
            ),
            currency_order=(
                Currency(curr) if (curr := data.get("Currency (Result)")) else Currency("USD")
            ),
            exchange_rate=(
                float(number)
                if ((number := data.get("Exchange rate")) and number != "Not available")
                else 1.0
            ),
            total_price=float(number) if (number := data.get("Total")) else -1.0,
        )
