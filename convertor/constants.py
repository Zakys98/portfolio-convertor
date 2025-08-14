from enum import StrEnum


class YAHOO_EXPORT(StrEnum):
    SYMBOL = "Symbol"
    TRADE_DATE = "Trade Date"
    QUANTITY = "Quantity"
    PURCHASE_PRICE = "Purchase Price"
    COMMISSION = "Commission"

    @classmethod
    def to_list(cls) -> list[str]:
        return [member for member in cls]
