from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

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


class XtbReader(Reader[XtbReport]):
    # Column indices for data extraction
    START_COL = 2
    END_COL_OFFSET = -4
    CURRENCY_ROW_INDEX = 5
    WORKSHEET = "CASH OPERATION HISTORY"

    # Data field indices after slicing
    TIME_INDEX = 0
    TICKER_INDEX = -2
    AMOUNT_INDEX = -1

    # Actions that contribute to deposit total
    DEPOSIT_ACTIONS = {
        XtbAction.DEP,
        XtbAction.FFI,
        XtbAction.FFIT,
        XtbAction.WT,
        XtbAction.SD,
    }

    def _extract_currency(self, row: tuple[Any, ...]) -> Currency:
        """Attempts to find the currency code in the specific header row."""
        try:
            currency_val = row[self.START_COL : self.END_COL_OFFSET][-2]
            return Currency(str(currency_val))
        except (IndexError, ValueError):
            return Currency.EUR

    def _parse_stock_transaction(
        self, values: tuple[Any, ...], currency: Currency
    ) -> XtbStock | None:
        """Parse stock purchase or sale transaction."""
        try:
            # Validate required fields
            if (
                len(values) >= 4
                and isinstance(values[0], datetime)
                and isinstance(values[1], str)
                and isinstance(values[2], str)
                and isinstance(values[3], (int, float))
            ):
                # values[3] is total_price and should be a number
                total_price = float(values[3]) if isinstance(values[3], (int, float)) else 0.0
                return XtbStock.from_dict(
                    (values[0], values[1], values[2], total_price), currency
                )
        except (ValueError, IndexError, AttributeError):
            pass
        return None

    def _parse_dividend(self, values: tuple[Any, ...], currency: Currency) -> Dividend | None:
        """Parse dividend transaction."""
        try:
            time = values[self.TIME_INDEX]
            ticker = values[self.TICKER_INDEX]
            amount = values[self.AMOUNT_INDEX]

            if (
                isinstance(time, datetime)
                and ticker is not None
                and isinstance(amount, float)
            ):
                return Dividend(
                    ticker=str(ticker),
                    time=time,
                    amount=float(amount),
                    currency=currency,
                )
        except (IndexError, ValueError):
            pass
        return None

    def _parse_deposit(self, values: tuple[Any, ...]) -> float:
        """Parse deposit/fee/tax transaction and return the amount."""
        try:
            amount = values[self.AMOUNT_INDEX]
            if isinstance(amount, float):
                return float(amount)
        except IndexError:
            pass
        return 0.0

    def read(self, input_file: Path) -> XtbReport:
        workbook = openpyxl.load_workbook(input_file)
        sheet = workbook[self.WORKSHEET]

        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            return XtbReport()

        currency = self._extract_currency(rows[self.CURRENCY_ROW_INDEX])
        report = XtbReport(deposit_currency=currency)

        for row in rows:
            data = row[self.START_COL : self.END_COL_OFFSET]

            if not data[0] or data[0] == "Type":
                continue

            try:
                if not isinstance(data[0], str):
                    continue
                action = XtbAction(data[0])
            except ValueError:
                continue

            values = data[1:]

            # Handle stock purchases
            if action == XtbAction.SP:
                if stock := self._parse_stock_transaction(values, currency):
                    report.buys.append(stock)

            # Handle stock sales
            elif action == XtbAction.SS:
                if stock := self._parse_stock_transaction(values, currency):
                    report.sells.append(stock)

            # Handle dividends
            elif action == XtbAction.DIV:
                if dividend := self._parse_dividend(values, currency):
                    report.dividends.append(dividend)

            # Handle deposits, fees, and taxes
            elif action in self.DEPOSIT_ACTIONS:
                report.deposit += self._parse_deposit(values)

        return report
