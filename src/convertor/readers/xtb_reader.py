from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import cast

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
    # Unused
    CT = "close trade"
    TRA = "transfer"
    SECF = "Sec Fee"
    SW = "swap"


class XtbReader(Reader):
    START_COL = 2
    END_COL_OFFSET = -4
    CURRENCY_ROW_INDEX = 5
    WORKSHEET = "CASH OPERATION HISTORY"

    def _extract_currency(self, row: tuple) -> Currency:
        """Attempts to find the currency code in the specific header row."""
        try:
            currency_val = row[self.START_COL : self.END_COL_OFFSET][-2]
            return Currency(str(currency_val))
        except (IndexError, ValueError):
            return Currency.EUR

    def read(self, input_file: Path) -> XtbReport:
        workbook = openpyxl.load_workbook(input_file)
        sheet = workbook[self.WORKSHEET]

        rows = list(sheet.iter_rows(values_only=True))
        currency = self._extract_currency(rows[self.CURRENCY_ROW_INDEX])
        report = XtbReport(deposit_currency=currency)

        ACTION_MAP = {
            XtbAction.SP: report.buys,
            XtbAction.SS: report.sells,
        }

        for row in rows:
            data = row[self.START_COL : self.END_COL_OFFSET]

            if not data[0] or data[0] == "Type":
                continue

            try:
                action = XtbAction(data[0])
            except ValueError:
                continue
            values = data[1:]

            if action in ACTION_MAP:
                validated_values = cast(tuple[datetime, str, str, str], values)
                ACTION_MAP[action].append(
                    XtbStock.from_dict(validated_values, currency)
                )

            elif (
                action == XtbAction.DIV
                and (time := values[0]) is not None
                and (amount := values[-1]) is not None
                and (ticker := values[-2]) is not None
                and isinstance(time, datetime)
                and isinstance(amount, float)
            ):
                report.dividends.append(
                    Dividend(
                        ticker=str(ticker),
                        time=time,
                        amount=float(amount),
                    )
                )

            elif (
                (
                    action == XtbAction.DEP
                    or action == XtbAction.FFI
                    or action == XtbAction.FFIT
                    or action == XtbAction.WT
                    or action == XtbAction.SD
                )
                and (deposit := values[-1]) is not None
                and isinstance(deposit, float)
            ):
                report.deposit += float(deposit)

        return report
