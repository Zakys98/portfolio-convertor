import json
from datetime import datetime

import pytest
from pydantic import ValidationError
from convertor.stocks.dividend import Dividend
from convertor.currency import Currency


def test_dividend_with_currency():
    d = Dividend(ticker="MSFT", time="2023-01-04 09:00:00", amount=5.50, currency=Currency.EUR)
    assert d.currency == Currency.EUR


def test_dividend_currency_is_required():
    with pytest.raises(ValidationError):
        Dividend(ticker="MSFT", time="2023-01-04 09:00:00", amount=5.50)


def test_dividend_date_from_string_time():
    d = Dividend(ticker="MSFT", time="2023-01-04 09:00:00", amount=5.50, currency=Currency.EUR)
    assert d.date == "2023-01-04"


def test_dividend_date_from_datetime_time():
    d = Dividend(ticker="JPM", time=datetime(2023, 2, 1, 15, 5, 55), amount=37.13, currency=Currency.CZK)
    assert d.date == "2023-02-01"


def test_dividend_date_is_serialized():
    d = Dividend(ticker="JPM", time="2023-02-01 15:05:55", amount=37.13, currency=Currency.CZK)
    assert d.model_dump()["date"] == "2023-02-01"
    assert json.loads(d.model_dump_json())["date"] == "2023-02-01"


def test_dividend_date_is_serialized_last():
    """Pydantic dumps computed fields after declared ones.

    Dividends reach the JSON output only, so this pins that file's key order.
    """
    d = Dividend(ticker="JPM", time="2023-02-01 15:05:55", amount=37.13, currency=Currency.CZK)
    assert list(d.model_dump()) == ["ticker", "time", "amount", "currency", "date"]


def test_dividend_date_is_not_settable():
    """date is computed from time, so it must not be independently assignable."""
    d = Dividend(
        ticker="JPM", time="2023-02-01 15:05:55", amount=37.13,
        currency=Currency.CZK, date="1999-12-31",
    )
    assert d.date == "2023-02-01"

    with pytest.raises(AttributeError):
        d.date = "1999-12-31"
