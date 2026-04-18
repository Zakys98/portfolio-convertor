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
