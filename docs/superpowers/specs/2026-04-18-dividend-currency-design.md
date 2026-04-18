# Dividend Currency Design

**Date:** 2026-04-18
**Status:** Approved

## Problem

The `Dividend` model stores `ticker`, `time`, and `amount` but no currency. Both input formats (Trading212 CSV, XTB XLSX) contain the currency of the received dividend, but it is silently dropped during parsing. This means consumers of the output cannot know what currency a dividend amount is in.

## Decision

Add a required `currency: Currency` field to `Dividend`. The field represents the currency of the received amount — i.e., what actually landed in the account.

## Data Model

```python
class Dividend(BaseModel):
    ticker: str
    time: str | datetime
    amount: float
    currency: Currency  # currency of the received amount
```

The field is required (no default). Any reader that constructs a `Dividend` must supply it explicitly.

## Reader Changes

### Trading212Reader

`Trading212Stock` already carries `currency_order` — the result currency of the transaction. Use it:

```python
return Dividend(
    ticker=stock.ticker,
    time=stock.time,
    amount=stock.total_price,
    currency=stock.currency_order,
)
```

### XtbReader

The reader already extracts the account currency from the worksheet header into `self.currency`. Pass it through:

```python
return Dividend(
    ticker=str(ticker),
    time=time,
    amount=float(amount),
    currency=self.currency,
)
```

## Output

Pydantic serializes all model fields automatically. Adding `currency` to `Dividend` propagates to both JSON and CSV outputs without changes to `report_manager.py`.

JSON example:
```json
{"ticker": "JPM", "time": "2023-02-01 15:05:55", "amount": 37.13, "currency": "CZK"}
```

## Test Changes

All existing dividend assertions in `test_trading212_reader.py` and `test_xtb_reader.py` must be updated to assert the `currency` field. No new test files are needed.

## Out of Scope

- Exchange rate tracking for dividends
- Storing the native stock currency separately from the received amount currency
- Changes to the Yahoo Finance output format (dividends are not included there)
