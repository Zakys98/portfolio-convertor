from pydantic import BaseModel, Field
from convertor.transaction import Transaction

class Report(BaseModel):
    transactions: list[Transaction] = Field(default_factory=list)

class Trading212Report(Report):
    pass

class XtbReport(Report):
    pass

class CoinmateReport(Report):
    pass
