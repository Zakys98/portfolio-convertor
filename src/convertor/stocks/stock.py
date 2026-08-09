from pydantic import BaseModel, computed_field

from convertor.constants import Standard, Yahoo
from convertor.currency import Currency
from convertor.utils import date_to_day


class Stock(BaseModel):
    ticker: str
    time: str
    quantity: float
    share_price: float
    currency_main: Currency
    total_price: float

    # mypy does not support decorators stacked on @property (prop-decorator);
    # the Pydantic plugin does not suppress it either. Pydantic itself handles
    # this pattern correctly at runtime.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> str:
        return date_to_day(self.time)

    def to_standard(self, type_: str) -> dict[str, str | float]:
        """Build one importer row. type_ is BUY or SELL, known only to the caller.

        Subclass fields (name, exchange_rate, ...) are deliberately excluded:
        the importer rejects any column outside Standard.
        """
        return {
            Standard.DATE: self.date,
            Standard.TYPE: type_,
            Standard.TICKER: self.ticker,
            Standard.QUANTITY: self.quantity,
            Standard.PRICE: self.share_price,
            Standard.CURRENCY: self.currency_main,
            Standard.FEES: "",
            Standard.NOTES: "",
            Standard.ISIN: "",
        }

    def to_yahoo(self) -> dict[str, str | float | int]:
        return {
            Yahoo.SYMBOL: self.ticker,
            Yahoo.TRADE_DATE: self.time,
            Yahoo.QUANTITY: self.quantity,
            Yahoo.PURCHASE_PRICE: self.share_price,
            Yahoo.COMMISSION: 0,
        }
