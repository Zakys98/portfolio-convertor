from typing import Self

from pydantic import BaseModel

from convertor.currency import Currency


class Trading212Stock(BaseModel):
    ticker: str
    name: str
    quantity: float
    share_price: float
    currency: Currency
    total_price: float

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            ticker=data.get("Ticker", ""),
            name=data.get("Name", ""),
            quantity=float(number) if (number := data.get("No. of shares")) else -1,
            share_price=float(number) if (number := data.get("Price / share")) else -1,
            currency=(
                Currency(curr) if (curr := data.get("Currency (Result)", "")) else Currency("USD")
            ),
            total_price=float(number) if (number := data.get("Total")) else -1,
        )
