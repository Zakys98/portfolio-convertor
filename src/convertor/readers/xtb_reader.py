from pathlib import Path
from enum import StrEnum

import openpyxl

from convertor.readers.reader import Reader
from convertor.currency import Currency
from convertor.stocks.dividend import Dividend
from convertor.stocks.xtb_stock import XtbStock
from convertor.report import XtbReport


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

    def read(self, input_file: Path) -> XtbReport:
        workbook = openpyxl.load_workbook(input_file)
        sheet = workbook["CASH OPERATION HISTORY"]

        rows = list(sheet.iter_rows(values_only=True))
        currency = self._extract_currency(rows[self.CURRENCY_ROW_INDEX])
        report = XtbReport(deposit_currency=currency)

        for row in rows:
            data = row[self.START_COL : self.END_COL_OFFSET]

            if not data[0]:
                continue

            action = data[0]
            values = data[1:]

            if action == XtbAction.SP:
                report.buys.append(XtbStock.from_dict(values, currency))

            elif action == XtbAction.SS:
                report.sells.append(XtbStock.from_dict(values, currency))

            elif (
                action == XtbAction.DIV
                and (ticker := values[-2] is not None)
                and (amount := values[-1] is not None)
            ):
                report.dividends.append(
                    Dividend(
                        ticker=str(ticker),
                        time=values[0].strftime("%Y%m%d"),
                        amount=float(amount),
                    )
                )

            elif (
                action == XtbAction.DEP
                or action == XtbAction.FFI
                or action == XtbAction.FFIT
                or action == XtbAction.WT
                or action == XtbAction.SD
            ) and (deposit := values[-1] is not None):
                report.deposit += float(deposit)

        return report
