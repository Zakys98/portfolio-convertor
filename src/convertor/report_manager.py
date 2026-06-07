import csv
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from convertor.transaction import Transaction, TransactionType
from convertor.report import Report


class ReportManager(BaseModel):
    reports: list[Report] = Field(default_factory=list)

    def transactions(self) -> list[dict[str, Any]]:
        transactions: list[dict[str, Any]] = []

        for report in self.reports:
            for tx in report.transactions:
                if tx.type in (TransactionType.CASH_IN, TransactionType.CASH_OUT):
                    continue
                    
                dumped = tx.model_dump(exclude_none=True)
                
                # Ghostfolio requires price > 0
                if dumped.get("price") == 0.0:
                    dumped["price"] = 0.0001
                    
                # Ghostfolio requires fees >= 0
                if "fees" in dumped and isinstance(dumped["fees"], (int, float)) and dumped["fees"] < 0:
                    dumped["fees"] = 0.0
                
                # the template requires these columns even if empty
                row = {
                    "date": dumped.get("date", ""),
                    "type": tx.type.value,
                    "ticker": dumped.get("ticker", ""),
                    "quantity": dumped.get("quantity", ""),
                    "price": dumped.get("price", ""),
                    "currency": tx.currency.value if tx.currency else "",
                    "fees": dumped.get("fees", ""),
                    "notes": dumped.get("notes", ""),
                    "toCurrency": tx.toCurrency.value if tx.toCurrency else "",
                    "toAmount": dumped.get("toAmount", ""),
                    "isin": dumped.get("isin", "")
                }
                transactions.append(row)

        transactions.sort(key=lambda x: x["date"])
        return transactions

    def write_csv(self, output_file: Path) -> None:
        transactions = self.transactions()
        if not transactions:
            output_file.write_text("", encoding="utf-8")
            return
            
        fieldnames = ['date', 'type', 'ticker', 'quantity', 'price', 'currency', 'fees', 'notes', 'toCurrency', 'toAmount', 'isin']
        with output_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(transactions)

    def write_json(self, output_file: Path) -> None:
        transactions = self.transactions()
        output_file.write_text(json.dumps(transactions, indent=4), encoding="utf-8")

    # Yahoo format is removed or broken right now, I'll leave a stub or remove it entirely as the user just wants the template.
    def dump_to_yahoo(self) -> list[dict[str, Any]]:
        return []
