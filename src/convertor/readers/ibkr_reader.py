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

    def read(self, input_file: Path) -> IbkrReport:
        report = IbkrReport()

        with input_file.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue

                section = row[0]

                if section == "Statement" and len(row) >= 4 and row[2] == "Base Currency":
                    try:
                        report.deposit_currency = Currency(row[3])
                    except ValueError:
                        pass

                elif (
                    section == "Change in NAV"
                    and len(row) >= 4
                    and row[1] == "Data"
                    and row[2] == "Deposits & Withdrawals"
                ):
                    try:
                        report.deposit += float(row[3])
                    except (ValueError, IndexError):
                        pass

                elif (
                    section == "Trades"
                    and len(row) >= 11
                    and row[1] == "Data"
                    and row[2] == "Order"
                    and row[3] == "Stocks"
                ):
                    try:
                        trade_currency = Currency(row[4])
                        symbol = row[5]
                        time = self._parse_datetime(row[6])
                        quantity = float(row[7])
                        share_price = float(row[8])
                        total_price = abs(float(row[10]))

                        stock = IbkrStock(
                            ticker=symbol,
                            time=time,
                            quantity=abs(quantity),
                            share_price=share_price,
                            currency_main=trade_currency,
                            total_price=total_price,
                        )

                        if quantity > 0:
                            report.buys.append(stock)
                        else:
                            report.sells.append(stock)
                    except (ValueError, IndexError):
                        pass

                elif (
                    section == "Dividends"
                    and len(row) >= 6
                    and row[1] == "Data"
                    and row[2] not in ("Total", "Total in CZK")
                ):
                    try:
                        div_currency = Currency(row[2])
                        time = self._parse_date(row[3])
                        ticker = self._ticker_from_description(row[4])
                        amount = float(row[5])

                        report.dividends.append(
                            Dividend(ticker=ticker, time=time, amount=amount, currency=div_currency)
                        )
                    except (ValueError, IndexError):
                        pass

        return report
