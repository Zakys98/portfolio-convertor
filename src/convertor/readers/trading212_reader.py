from csv import DictReader
from enum import StrEnum
from pathlib import Path

from convertor.readers.reader import Reader
from convertor.report import Trading212Report
from convertor.transaction import Transaction, TransactionType
from convertor.currency import Currency
from convertor.utils import date_to_string, parse_float


class T212Action(StrEnum):
    DEP = "Deposit"
    DIV = "Dividend (Dividend)"
    MB = "Market buy"
    MS = "Market sell"
    LB = "Limit buy"
    LS = "Limit sell"


class Trading212Reader(Reader[Trading212Report]):
    BUY_ACTIONS = {T212Action.MB, T212Action.LB}
    SELL_ACTIONS = {T212Action.MS, T212Action.LS}

    def read(self, input_file: Path) -> Trading212Report:
        report = Trading212Report()

        with input_file.open("r") as csvfile:
            reader = DictReader(csvfile)

            for row in reader:
                action_str = row.get("Action", "")

                if not action_str:
                    continue

                try:
                    action = T212Action(action_str)
                except ValueError:
                    continue

                time = date_to_string(row.get("Time", ""))
                ticker = row.get("Ticker", "")
                isin = row.get("ISIN", "")
                currency_str = row.get("Currency (Price / share)", "")
                
                # Disambiguate tickers listed on multiple exchanges
                if ticker == "ASML":
                    if isin == "USN070592100" or currency_str == "USD":
                        ticker = "ASML.US"
                    elif isin == "NL0010273215" or currency_str == "EUR":
                        ticker = "ASML.AS"
                        
                currency = Currency(currency_str) if currency_str else None
                
                quantity = parse_float(row.get("No. of shares"))
                price = parse_float(row.get("Price / share"))
                total = parse_float(row.get("Total"))
                
                quantity = quantity if quantity != -1.0 else None
                price = price if price != -1.0 else None
                total = total if total != -1.0 else None

                if action in self.BUY_ACTIONS:
                    tx = Transaction(
                        date=time,
                        type=TransactionType.BUY,
                        ticker=ticker,
                        quantity=quantity,
                        price=price,
                        currency=currency,
                        notes=action.value
                    )
                    report.transactions.append(tx)

                elif action in self.SELL_ACTIONS:
                    tx = Transaction(
                        date=time,
                        type=TransactionType.SELL,
                        ticker=ticker,
                        quantity=quantity,
                        price=price,
                        currency=currency,
                        notes=action.value
                    )
                    report.transactions.append(tx)

                elif action == T212Action.DIV:
                    tx = Transaction(
                        date=time,
                        type=TransactionType.CASH_IN,
                        ticker=ticker,
                        price=total,
                        currency=currency,
                        notes="Dividend"
                    )
                    report.transactions.append(tx)

                elif action == T212Action.DEP:
                    tx_type = TransactionType.CASH_IN if total and total > 0 else TransactionType.CASH_OUT
                    tx = Transaction(
                        date=time,
                        type=tx_type,
                        price=abs(total) if total else 0.0,
                        currency=currency,
                        notes="Deposit/Withdrawal"
                    )
                    report.transactions.append(tx)

        return report
