from collections.abc import Sequence
from pathlib import Path
from enum import StrEnum

import openpyxl

from .reader import Reader
from convertor.currency import Currency
from convertor.stocks.xtb_stock import XtbStock


class XtbAction(StrEnum):
    DEP = "deposit"
    DIV = "DIVIDENT"
    FFI = "Free-funds Interest"
    FFIT = "Free-funds Interest Tax"
    SD = "Stamp Duty"
    SP = "Stock purchase"
    SS = "Stock sale"
    WT = "Withholding Tax"


class XtbReader(Reader):
    START_COL = 2
    END_COL_OFFSET = -4
    CURRENCY_ROW_INDEX = 5

    def _extract_currency(self, row: tuple) -> Currency:
        """Attempts to find the currency code in the specific header row."""
        try:
            currency_val = row[self.START_COL : self.END_COL_OFFSET][-2]
            return Currency(str(currency_val))
        except (IndexError, ValueError):
            return Currency.EUR

    def read(
        self, input_file: Path
    ) -> tuple[Sequence[XtbStock], Sequence[XtbStock], float]:
        buys: list[XtbStock] = []
        sells: list[XtbStock] = []
        deposits: float = 0.0

        workbook = openpyxl.load_workbook(input_file)
        sheet = workbook["CASH OPERATION HISTORY"]

        rows = list(sheet.iter_rows(values_only=True))
        currency = self._extract_currency(rows[self.CURRENCY_ROW_INDEX])

        for row in rows:
            data = row[self.START_COL : self.END_COL_OFFSET]

            if not data[0]:
                continue

            action = data[0]
            values = data[1:]

            if action == XtbAction.SP:
                buys.append(XtbStock.from_dict(values, currency))

            elif action == XtbAction.SS:
                sells.append(XtbStock.from_dict(values, currency))

            elif action == XtbAction.DEP:
                deposits += float(str(values[-1]) or 0)

        return buys, sells, deposits
