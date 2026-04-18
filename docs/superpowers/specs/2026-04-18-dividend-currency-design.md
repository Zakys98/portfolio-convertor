# Dividend Currency Design

**Date:** 2026-04-18
**Status:** Approved

## Problem

The `Dividend` model stores `ticker`, `time`, and `amount` but no currency. Both input formats (Trading212 CSV, XTB XLSX) contain the currency of the received dividend, but it is silently dropped during parsing. This means consumers of the output cannot know what currency a dividend amount is in.

## Decision

Add a required `currency: Currency` field to `Dividend`. The field represents the currency of the received amount — i.e., what actually landed in the account.

## Data Model

```python
from convertor.currency import Currency  # must be added to dividend.py

class Dividend(BaseModel):
    ticker: str
    time: str | datetime
    amount: float
    currency: Currency  # currency of the received amount
```

The field is required (no default). Any reader that constructs a `Dividend` must supply it explicitly. `dividend.py` must add the `Currency` import.

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

**Pending code change.** `currency` is a local variable in `read()`, extracted from the worksheet header via `self._extract_currency(rows[self.CURRENCY_ROW_INDEX])`. The current `_parse_dividend` signature is:

```python
def _parse_dividend(self, values: tuple[Any, ...]) -> Dividend | None:
```

It must be updated to accept `currency: Currency` as a second parameter, matching the pattern already used by `_parse_stock_transaction`:

```python
def _parse_dividend(self, values: tuple[Any, ...], currency: Currency) -> Dividend | None:
    ...
    return Dividend(ticker=str(ticker), time=time, amount=float(amount), currency=currency)
```

The call site in `read()` (currently `self._parse_dividend(values)`) must also be updated:
```python
if dividend := self._parse_dividend(values, currency):
```

XTB worksheets expose only one currency (the account currency), so dividends are assumed to be paid in the account currency. This is correct for the data available; if a broker ever pays in a different currency, that information is not present in the XTB export.

## Output

Pydantic serializes all model fields automatically. Adding `currency` to `Dividend` propagates to both JSON and CSV outputs without changes to `report_manager.py`.

JSON example:
```json
{"ticker": "JPM", "time": "2023-02-01 15:05:55", "amount": 37.13, "currency": "CZK"}
```

## Test Changes

All existing dividend assertions in `test_trading212_reader.py` and `test_xtb_reader.py` must be updated to assert the `currency` field. No new test files are needed.

**Trading212 fixtures**: the following test functions in `test_trading212_reader.py` build CSV strings that include dividend rows and must add a `Currency (Result)` column with a known non-default value (e.g., `CZK`):
- `mock_csv`
- `test_multiple_dividends`
- `test_comprehensive_all_action_types`
- `test_dividend_without_ticker`

Without this column `Trading212Stock.from_dict` falls back to `Currency.USD`, testing the fallback path rather than actual forwarding. Assertions must check the explicit value from the fixture.

**XTB fixtures**: `_extract_currency` slices `row[2:-4][-2]`, which for a 12-column row equals absolute index 6 (zero-based). All XTB test fixtures that include dividend rows must have their `CURRENCY_ROW_INDEX` row widened to 12 columns with the currency value at **index 6 only**. The following tests require this fix:
- `mock_xlsx` (shared fixture — currently 7 columns, triggers `IndexError` fallback)
- `test_multiple_transactions_same_type` (inline fixture, 12 columns but `None` at index 6)
- `test_midnight_and_edge_dates` (inline fixture, same issue)

Correct 12-column `CURRENCY_ROW_INDEX` row with `EUR` at index 6:

```python
[None, None, None, None, None, None, "EUR", None, None, None, None, None]
```

Dividend assertions must verify the extracted `currency` value matches the fixture, not just assume the `Currency.EUR` fallback.

## Out of Scope

- Exchange rate tracking for dividends
- Storing the native stock currency separately from the received amount currency
- Changes to the Yahoo Finance output format (dividends are not included there)
