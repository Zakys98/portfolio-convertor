from pydantic import BaseModel

from convertor.currency import Currency
from convertor.constants import Yahoo


class Stock(BaseModel):
    ticker: str
    time: str
    quantity: float
    share_price: float
    currency_main: Currency
    total_price: float

    def to_yahoo(self) -> dict[str, str | float | int]:
        return {
            Yahoo.SYMBOL: self.ticker,
            Yahoo.TRADE_DATE: self.time,
            Yahoo.QUANTITY: self.quantity,
            Yahoo.PURCHASE_PRICE: self.share_price,
            Yahoo.COMMISSION: 0,
        }
