from pydantic import BaseModel

from convertor.currency import Currency
from convertor.constants import YAHOO_EXPORT


class Stock(BaseModel):
    ticker: str
    time: str
    quantity: float
    share_price: float
    currency_main: Currency
    total_price: float

    def to_yahoo(self) -> dict[str, str]:
        return {
            YAHOO_EXPORT.SYMBOL: self.ticker,
            YAHOO_EXPORT.TRADE_DATE: self.time,
            YAHOO_EXPORT.QUANTITY: self.quantity,
            YAHOO_EXPORT.PURCHASE_PRICE: self.share_price,
            YAHOO_EXPORT.COMMISSION: 0,
        }
