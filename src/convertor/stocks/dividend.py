from pydantic import BaseModel, field_validator
from datetime import datetime

from convertor.currency import Currency
from convertor.utils import date_to_string


class Dividend(BaseModel):
    ticker: str
    time: str | datetime  # datetime type is just for input and it is converted to str
    amount: float
    currency: Currency

    @field_validator("time", mode="before")
    @classmethod
    def format_date(cls, value: str | datetime) -> str:
        return date_to_string(value)
