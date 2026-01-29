from pydantic import BaseModel, Field

from convertor.currency import Currency
from convertor.stocks.stock import Stock
from convertor.stocks.xtb_stock import XtbStock
from convertor.stocks.trading212_stock import Trading212Stock
from convertor.stocks.dividend import Dividend


class Report[T: Stock](BaseModel):
    buys: list[T] = Field(default_factory=list)
    sells: list[T] = Field(default_factory=list)
    dividends: list[Dividend] = Field(default_factory=list)
    deposit: float = 0.0
    deposit_currency: Currency = Currency.CZK


class Trading212Report(Report[Trading212Stock]):
    pass


class XtbReport(Report[XtbStock]):
    pass
