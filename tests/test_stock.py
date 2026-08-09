"""Unit tests for the Stock model's computed date field."""

from datetime import datetime

import pytest

from convertor.currency import Currency
from convertor.stocks.ibkr_stock import IbkrStock
from convertor.stocks.stock import Stock
from convertor.stocks.trading212_stock import Trading212Stock
from convertor.stocks.xtb_stock import XtbStock


def _stock(time: str) -> Stock:
    return Stock(
        ticker="DVN",
        time=time,
        quantity=1.0,
        share_price=45.17,
        currency_main=Currency.USD,
        total_price=45.17,
    )


def test_stock_date_from_time():
    assert _stock("2023-03-16 16:21:03").date == "2023-03-16"


def test_stock_date_is_serialized():
    assert _stock("2023-03-16 16:21:03").model_dump()["date"] == "2023-03-16"


def test_stock_date_serialized_last():
    """Pydantic serializes computed fields after declared ones.

    This is the JSON output's key order, which is user-visible. The CSV does
    not depend on it -- write_csv declares its columns via Standard.to_list().
    """
    assert list(_stock("2023-03-16 16:21:03").model_dump())[-1] == "date"


def test_stock_date_with_malformed_time():
    """A stock built from bad broker data must still serialize."""
    assert _stock("").date == ""


def test_xtb_stock_inherits_date():
    stock = XtbStock.from_dict(
        (datetime(2023, 3, 16, 16, 21, 3), "OPEN BUY 2 @ 45.17", "DVN", 90.34),
        Currency.USD,
    )
    assert stock.date == "2023-03-16"


def test_trading212_stock_inherits_date():
    stock = Trading212Stock.from_dict(
        {
            "Ticker": "COIN",
            "Name": "Coinbase",
            "Time": "2023-04-28 13:37:07",
            "No. of shares": "1",
            "Price / share": "53.49",
            "Currency (Price / share)": "USD",
            "Currency (Result)": "CZK",
            "Exchange rate": "0.04685857",
            "Total": "1143.23",
        }
    )
    assert stock.date == "2023-04-28"


def test_subclass_date_serialized_after_all_declared_fields():
    """Trading212Stock is the only model declaring fields after the base.

    So it is the one case distinguishing "after the base's fields" from "after
    ALL declared fields", which is what the JSON output's key order shows.
    """
    stock = Trading212Stock.from_dict(
        {
            "Ticker": "COIN",
            "Name": "Coinbase",
            "Time": "2023-04-28 13:37:07",
            "No. of shares": "1",
            "Price / share": "53.49",
            "Currency (Price / share)": "USD",
            "Currency (Result)": "CZK",
            "Exchange rate": "0.04685857",
            "Total": "1143.23",
        }
    )
    assert list(stock.model_dump()) == [
        "ticker", "time", "quantity", "share_price", "currency_main",
        "total_price", "name", "currency_order", "exchange_rate", "date",
    ]


def test_stock_date_is_not_settable():
    """Mirrors the Dividend test: the two copies of the property can drift."""
    stock = _stock("2023-03-16 16:21:03")
    with pytest.raises(AttributeError):
        stock.date = "1999-12-31"


def test_ibkr_stock_inherits_date():
    stock = IbkrStock(
        ticker="BAC",
        time="2023-08-24 13:30:48",
        quantity=1.0,
        share_price=28.49,
        currency_main=Currency.USD,
        total_price=636.25,
    )
    assert stock.date == "2023-08-24"


def test_to_standard_shape_and_values():
    """The importer accepts only these columns, in this order."""
    row = _stock("2023-03-16 16:21:03").to_standard("BUY")
    assert list(row) == [
        "date", "type", "ticker", "quantity", "price", "currency", "fees", "notes", "isin",
    ]
    assert row == {
        "date": "2023-03-16",
        "type": "BUY",
        "ticker": "DVN",
        "quantity": 1.0,
        "price": 45.17,
        "currency": Currency.USD,
        "fees": "",
        "notes": "",
        "isin": "",
    }


def test_to_standard_excludes_internal_fields():
    """Every one of these was rejected by the importer as an unknown column."""
    row = _stock("2023-03-16 16:21:03").to_standard("SELL")
    rejected = {
        "time", "share_price", "currency_main", "total_price",
        "name", "currency_order", "exchange_rate", "amount",
    }
    assert rejected.isdisjoint(row)


def test_to_standard_subclass_drops_extra_fields():
    """Trading212Stock's extra fields must not leak into the import row."""
    stock = Trading212Stock.from_dict(
        {
            "Ticker": "COIN",
            "Name": "Coinbase",
            "Time": "2023-04-28 13:37:07",
            "No. of shares": "1",
            "Price / share": "53.49",
            "Currency (Price / share)": "USD",
            "Currency (Result)": "CZK",
            "Exchange rate": "0.04685857",
            "Total": "1143.23",
        }
    )
    assert list(stock.to_standard("BUY")) == [
        "date", "type", "ticker", "quantity", "price", "currency", "fees", "notes", "isin",
    ]
    assert stock.to_standard("BUY")["price"] == 53.49


def test_to_yahoo_unaffected():
    """The Yahoo export has its own fixed fieldnames and must not gain date."""
    assert "date" not in _stock("2023-03-16 16:21:03").to_yahoo()
