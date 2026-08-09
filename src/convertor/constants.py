from enum import StrEnum


class FileExtension(StrEnum):
    CSV = ".csv"
    JSON = ".json"
    XLSX = ".xlsx"


class Standard(StrEnum):
    """Columns accepted by the portfolio importer.

    The importer validates the header strictly and rejects any column it does
    not know, so this is a whitelist rather than a suggested minimum. fees,
    notes and isin are optional and currently always emitted empty -- no reader
    captures them yet.
    """

    DATE = "date"
    TYPE = "type"
    TICKER = "ticker"
    QUANTITY = "quantity"
    PRICE = "price"
    CURRENCY = "currency"
    FEES = "fees"
    NOTES = "notes"
    ISIN = "isin"

    @classmethod
    def to_list(cls) -> list[str]:
        return [member for member in cls]


class Yahoo(StrEnum):
    SYMBOL = "Symbol"
    TRADE_DATE = "Trade Date"
    QUANTITY = "Quantity"
    PURCHASE_PRICE = "Purchase Price"
    COMMISSION = "Commission"

    @classmethod
    def to_list(cls) -> list[str]:
        return [member for member in cls]
