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

    def read(self, input_file: Path) -> Sequence[XtbStock]:
        buys: list[XtbStock] = []
        sells: list[XtbStock] = []
        deposits: float = 0.0

        workbook = openpyxl.load_workbook(input_file)
        history = workbook["CASH OPERATION HISTORY"]

        for i, row in enumerate(history.iter_rows(values_only=True)):
            line = row[2:-4]
            if line[0] is None:
                continue
            if i == 5:
                currency = Currency(line[-2])

        for row in history.iter_rows(values_only=True):
            line = row[2:-4]
            if not line[0]:
                continue

            action = line[0]
            line = line[1:]

            if action == XtbAction.SP:
                stock = XtbStock.from_dict(line, currency)
                buys.insert(0, stock)

            elif action == XtbAction.SS:
                stock = XtbStock.from_dict(line, currency)
                sells.insert(0, stock)

            elif action == XtbAction.DEP:
                deposits += float(str(line[-1]))

        return buys
