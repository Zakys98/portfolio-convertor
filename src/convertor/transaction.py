from enum import StrEnum
from pydantic import BaseModel, Field

from convertor.currency import Currency


class TransactionType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    FEE = "FEE"
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"
    FX_CONVERT = "FX_CONVERT"


class Transaction(BaseModel):
    date: str
    type: TransactionType
    ticker: str | None = None
    quantity: float | None = None
    price: float | None = None
    currency: Currency | None = None
    fees: float | None = None
    notes: str | None = None
    toCurrency: Currency | None = None
    toAmount: float | None = None
    isin: str | None = None
