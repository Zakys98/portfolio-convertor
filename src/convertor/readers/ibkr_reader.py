import csv
from datetime import datetime
from pathlib import Path

from convertor.currency import Currency
from convertor.readers.reader import Reader
from convertor.report import IbkrReport
from convertor.stocks.dividend import Dividend
from convertor.stocks.ibkr_stock import IbkrStock
from convertor.utils import date_to_string

IBKR_DATETIME_FORMAT = "%Y-%m-%d, %H:%M:%S"
IBKR_DATE_FORMAT = "%Y-%m-%d"


class IbkrReader(Reader[IbkrReport]):

    def _parse_datetime(self, value: str) -> str:
        try:
            return date_to_string(datetime.strptime(value.strip(), IBKR_DATETIME_FORMAT))
        except ValueError:
            return value

    def _parse_date(self, value: str) -> str:
        try:
            return date_to_string(datetime.strptime(value.strip(), IBKR_DATE_FORMAT))
        except ValueError:
            return value

    def _ticker_from_description(self, description: str) -> str:
        return description.split("(")[0].strip()

    def _parse_trade(self, row: list[str]) -> IbkrStock | None:
        try:
            return IbkrStock(
                ticker=row[5],
                time=self._parse_datetime(row[6]),
                quantity=abs(float(row[7])),
                share_price=float(row[8]),
                currency_main=Currency(row[4]),
                total_price=abs(float(row[10])),
            )
        except (ValueError, IndexError):
            return None

    def _parse_dividend(self, row: list[str]) -> Dividend | None:
        try:
            return Dividend(
                ticker=self._ticker_from_description(row[4]),
                time=self._parse_date(row[3]),
                amount=float(row[5]),
                currency=Currency(row[2]),
            )
        except (ValueError, IndexError):
            return None

    def read(self, input_file: Path) -> IbkrReport:
        report = IbkrReport()

        with input_file.open("r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if not row:
                    continue

                match row[0]:
                    case "Statement" if len(row) >= 4 and row[2] == "Base Currency":
                        try:
                            report.deposit_currency = Currency(row[3])
                        except ValueError:
                            pass

                    case "Change in NAV" if len(row) >= 4 and row[1] == "Data" and row[2] == "Deposits & Withdrawals":
                        try:
                            report.deposit += float(row[3])
                        except (ValueError, IndexError):
                            pass

                    case "Trades" if len(row) >= 11 and row[1] == "Data" and row[2] == "Order" and row[3] == "Stocks":
                        if stock := self._parse_trade(row):
                            if float(row[7]) > 0:
                                report.buys.append(stock)
                            else:
                                report.sells.append(stock)

                    case "Dividends" if len(row) >= 6 and row[1] == "Data" and row[2] not in ("Total", "Total in CZK"):
                        if dividend := self._parse_dividend(row):
                            report.dividends.append(dividend)

        return report
