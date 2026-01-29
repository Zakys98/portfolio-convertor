from pydantic import BaseModel


class Dividend(BaseModel):
    ticker: str
    time: str
    amount: float
