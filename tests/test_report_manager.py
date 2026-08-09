"""Unit tests for ReportManager output.

The CSV output targets a strict importer: it accepts only the columns in
Standard and rejects any other, so these tests pin the exact header.
"""

import csv
import json

from convertor.constants import Standard
from convertor.currency import Currency
from convertor.report import Report
from convertor.report_manager import ReportManager
from convertor.stocks.dividend import Dividend
from convertor.stocks.stock import Stock


def _stock(ticker: str, time: str) -> Stock:
    return Stock(
        ticker=ticker,
        time=time,
        quantity=1.0,
        share_price=45.17,
        currency_main=Currency.USD,
        total_price=45.17,
    )


def _manager() -> ReportManager:
    report = Report[Stock](
        buys=[_stock("DVN", "2023-03-16 16:21:03")],
        sells=[_stock("COIN", "2023-04-28 13:37:07")],
        dividends=[
            Dividend(ticker="JPM", time="2023-02-01 15:05:55", amount=37.13, currency=Currency.CZK)
        ],
        deposit=100.0,
        deposit_currency=Currency.CZK,
    )
    return ReportManager(reports=[report])


def _header(path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()[0].split(",")


def test_csv_header_is_exactly_the_standard_columns(tmp_path):
    """The importer rejects unknown columns, so the header must match exactly."""
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    assert _header(output) == [
        "date", "type", "ticker", "quantity", "price", "currency", "fees", "notes", "isin",
    ]
    assert _header(output) == Standard.to_list()


def test_csv_drops_internal_columns(tmp_path):
    """These were previously emitted and the importer rejected every one."""
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    rejected = {
        "time", "share_price", "currency_main", "total_price",
        "name", "currency_order", "exchange_rate", "amount",
    }
    assert rejected.isdisjoint(_header(output))


def test_csv_contains_only_buys_and_sells(tmp_path):
    """Dividends are omitted: the importer derives them itself."""
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    with output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [row["type"] for row in rows] == ["BUY", "SELL"]
    assert "JPM" not in {row["ticker"] for row in rows}


def test_csv_rows_are_sorted_oldest_first(tmp_path):
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    with output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [row["date"] for row in rows] == ["2023-03-16", "2023-04-28"]


def test_csv_row_values(tmp_path):
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    with output.open(newline="", encoding="utf-8") as file:
        first = next(csv.DictReader(file))
    assert first == {
        "date": "2023-03-16",
        "type": "BUY",
        "ticker": "DVN",
        "quantity": "1.0",
        "price": "45.17",
        "currency": "USD",
        "fees": "",
        "notes": "",
        "isin": "",
    }


def test_csv_sorts_across_multiple_reports(tmp_path):
    """Sorting is global, not per-report."""
    older = Report[Stock](buys=[_stock("AAA", "2022-01-01 09:00:00")])
    newer = Report[Stock](buys=[_stock("BBB", "2024-01-01 09:00:00")])
    output = tmp_path / "out.csv"
    ReportManager(reports=[newer, older]).write_csv(output)
    with output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [row["ticker"] for row in rows] == ["AAA", "BBB"]


def test_empty_report_writes_header_only(tmp_path):
    """A header-only file is still valid for import, unlike an empty one."""
    output = tmp_path / "out.csv"
    ReportManager().write_csv(output)
    assert _header(output) == Standard.to_list()
    assert output.read_text(encoding="utf-8").splitlines()[1:] == []


def test_json_keeps_full_detail_including_dividends(tmp_path):
    """JSON is the debugging view: it keeps every field and every kind."""
    output = tmp_path / "out.json"
    _manager().write_json(output)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["buys"][0]["date"] == "2023-03-16"
    assert data["sells"][0]["date"] == "2023-04-28"
    assert data["dividends"][0]["date"] == "2023-02-01"
    assert data["buys"][0]["share_price"] == 45.17
    assert data["deposits"] == {"CZK": 100.0}
