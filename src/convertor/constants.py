from enum import StrEnum


class PathExtensin(StrEnum):
    CSV = ".csv"
    XLSX = ".xlsx"


class Yahoo(StrEnum):
    SYMBOL = "Symbol"
    TRADE_DATE = "Trade Date"
    QUANTITY = "Quantity"
    PURCHASE_PRICE = "Purchase Price"
    COMMISSION = "Commission"

    @classmethod
    def to_list(cls) -> list[str]:
        return [member for member in cls]
