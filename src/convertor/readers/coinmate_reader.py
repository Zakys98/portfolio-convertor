from csv import DictReader
from pathlib import Path

from convertor.readers.reader import Reader
from convertor.report import CoinmateReport
from convertor.transaction import Transaction, TransactionType
from convertor.currency import Currency
from convertor.utils import date_to_string, parse_float
from convertor.exchange_rate import CNBRateFetcher

class CoinmateReader(Reader[CoinmateReport]):

    def read(self, input_file: Path) -> CoinmateReport:
        report = CoinmateReport()

        with input_file.open("r", encoding="utf-8-sig") as csvfile:
            reader = DictReader(csvfile, delimiter=";")

            for row in reader:
                action_str = row.get("Typ", "")
                if not action_str:
                    continue

                action_str = action_str.upper()
                time = date_to_string(row.get("Datum", ""))
                
                # Check status
                if row.get("Status", "") not in ("OK", "COMPLETED"):
                    continue

                if action_str in ("MARKET_BUY", "BUY", "QUICK_BUY"):
                    ticker = row.get("Částka měny", "")
                    currency_str = row.get("Cena měny", "") or row.get("Celkem měny", "")
                    currency = Currency(currency_str) if currency_str else None
                    
                    quantity = abs(parse_float(row.get("Částka", "0")))
                    price = parse_float(row.get("Cena", "0"))
                    fees = parse_float(row.get("Poplatek", "0"))
                    
                    if currency == Currency.EUR:
                        rate = CNBRateFetcher.get_eur_to_usd(time)
                        price = price * rate
                        fees = fees * rate
                        currency = Currency.USD
                        
                    if quantity > 0:
                        tx = Transaction(
                            date=time,
                            type=TransactionType.BUY,
                            ticker=ticker,
                            quantity=quantity,
                            price=price,
                            currency=currency,
                            fees=fees if fees != -1.0 else 0.0,
                            notes=action_str
                        )
                        report.transactions.append(tx)

                elif action_str in ("MARKET_SELL", "SELL"):
                    ticker = row.get("Částka měny", "")
                    currency_str = row.get("Cena měny", "") or row.get("Celkem měny", "")
                    currency = Currency(currency_str) if currency_str else None
                    
                    quantity = abs(parse_float(row.get("Částka", "0")))
                    price = parse_float(row.get("Cena", "0"))
                    fees = parse_float(row.get("Poplatek", "0"))
                    
                    if currency == Currency.EUR:
                        rate = CNBRateFetcher.get_eur_to_usd(time)
                        price = price * rate
                        fees = fees * rate
                        currency = Currency.USD
                        
                    if quantity > 0:
                        tx = Transaction(
                            date=time,
                            type=TransactionType.SELL,
                            ticker=ticker,
                            quantity=quantity,
                            price=price,
                            currency=currency,
                            fees=fees if fees != -1.0 else 0.0,
                            notes=action_str
                        )
                        report.transactions.append(tx)

                elif action_str in ("DEPOSIT", "WITHDRAWAL"):
                    currency_str = row.get("Částka měny", "")
                    try:
                        currency = Currency(currency_str) if currency_str else None
                    except ValueError:
                        # Sometimes crypto deposits/withdrawals happen, we map them as fiat CASH_IN/OUT for tracking purposes or just ignore?
                        # Since we filter out CASH_IN/OUT later anyway, it's fine.
                        currency = None
                    
                    amount = parse_float(row.get("Částka", "0"))
                    fees = parse_float(row.get("Poplatek", "0"))
                    
                    tx_type = TransactionType.CASH_IN if action_str == "DEPOSIT" else TransactionType.CASH_OUT
                    
                    tx = Transaction(
                        date=time,
                        type=tx_type,
                        price=abs(amount),
                        currency=currency,
                        fees=fees if fees != -1.0 else 0.0,
                        notes=action_str
                    )
                    report.transactions.append(tx)

        return report
