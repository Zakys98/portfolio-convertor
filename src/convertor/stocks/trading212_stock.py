from typing import Self

from convertor.currency import Currency
from convertor.stocks.stock import Stock


class Trading212Stock(Stock):
    name: str
    currency_order: Currency
    exchange_rate: float

    @classmethod
    def _parse_float(cls, value: str | None, default: float = -1.0) -> float:
        """Parse a string value to float, returning default if invalid."""
        if not value:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @classmethod
    def _parse_currency(cls, value: str | None, default: str = "USD") -> Currency:
        """Parse a currency string, returning default currency if invalid."""
        if not value:
            return Currency(default)
        try:
            return Currency(value)
        except (ValueError, TypeError):
            return Currency(default)

    @classmethod
    def _parse_exchange_rate(cls, value: str | None) -> float:
        """Parse exchange rate, handling 'Not available' special case."""
        if not value or value == "Not available":
            return 1.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 1.0

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            ticker=data.get("Ticker", ""),
            name=data.get("Name", ""),
            time=data.get("Time", ""),
            quantity=cls._parse_float(data.get("No. of shares")),
            share_price=cls._parse_float(data.get("Price / share")),
            currency_main=cls._parse_currency(data.get("Currency (Price / share)")),
            currency_order=cls._parse_currency(data.get("Currency (Result)")),
            exchange_rate=cls._parse_exchange_rate(data.get("Exchange rate")),
            total_price=cls._parse_float(data.get("Total")),
        )
