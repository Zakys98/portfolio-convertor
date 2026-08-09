from pydantic import BaseModel, computed_field, field_validator
from datetime import datetime

from convertor.currency import Currency
from convertor.utils import date_to_day, date_to_string


class Dividend(BaseModel):
    ticker: str
    time: str | datetime  # datetime type is just for input and it is converted to str
    amount: float
    currency: Currency

    # mypy does not support decorators stacked on @property (prop-decorator);
    # the Pydantic plugin does not suppress it either. Pydantic itself handles
    # this pattern correctly at runtime.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> str:
        return date_to_day(self.time)

    @field_validator("time", mode="before")
    @classmethod
    def format_date(cls, value: str | datetime) -> str:
        return date_to_string(value)
