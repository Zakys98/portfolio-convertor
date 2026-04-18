# Dividend Currency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a required `currency: Currency` field to `Dividend` representing the received amount's currency, and thread it through both readers and their tests.

**Architecture:** Three sequential tasks: (1) update the `Dividend` model, (2) fix `Trading212Reader` and its tests, (3) fix `XtbReader` and its tests. Each task leaves the test suite passing before moving on. After Task 1, reader tests will fail with `ValidationError` (expected) — that is the TDD signal to proceed to Tasks 2 and 3.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, uv

---

## File Map

| File | Change |
|------|--------|
| `src/convertor/stocks/dividend.py` | Add `currency: Currency` field + import |
| `src/convertor/readers/trading212_reader.py` | Pass `stock.currency_order` to `Dividend` |
| `src/convertor/readers/xtb_reader.py` | Add `currency` param to `_parse_dividend`; update call site |
| `tests/test_dividend.py` | New — unit tests for Dividend model |
| `tests/readers/test_trading212_reader.py` | Add `Currency (Result)` column to fixtures; add `currency` assertions |
| `tests/readers/test_xtb_reader.py` | Fix `CURRENCY_ROW_INDEX` rows; add `currency` assertions |

---

## Task 1: Add `currency` to Dividend model

**Files:**
- Create: `tests/test_dividend.py`
- Modify: `src/convertor/stocks/dividend.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dividend.py`:

```python
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
```

- [ ] **Step 2: Run to confirm the first test fails**

```bash
uv run pytest tests/test_dividend.py -v
```

Expected: `test_dividend_with_currency` FAILS (`AttributeError` — Pydantic ignores unknown fields by default, so `d.currency` does not exist). `test_dividend_currency_is_required` PASSES — constructing `Dividend` without currency currently succeeds (no field means no validation). This is correct pre-implementation state.

- [ ] **Step 3: Update Dividend model**

Replace the entire contents of `src/convertor/stocks/dividend.py`:

```python
from pydantic import BaseModel, field_validator
from datetime import datetime

from convertor.currency import Currency
from convertor.utils import date_to_string


class Dividend(BaseModel):
    ticker: str
    time: str | datetime  # datetime type is just for input and it is converted to str
    amount: float
    currency: Currency

    @field_validator("time", mode="before")
    @classmethod
    def format_date(cls, value: str | datetime) -> str:
        return date_to_string(value)
```

- [ ] **Step 4: Run Dividend tests — expect PASS**

```bash
uv run pytest tests/test_dividend.py -v
```

Expected: both PASS

- [ ] **Step 5: Confirm reader tests now fail (expected)**

```bash
uv run pytest tests/readers/ -v 2>&1 | head -40
```

Expected: failures with `ValidationError: 1 validation error for Dividend — currency: Field required`. This is correct — the readers don't yet pass currency. Proceed to Task 2.

- [ ] **Step 6: Commit**

```bash
git add tests/test_dividend.py src/convertor/stocks/dividend.py
git commit -m "feat: add required currency field to Dividend model"
```

---

## Task 2: Update Trading212Reader and its tests

**Files:**
- Modify: `tests/readers/test_trading212_reader.py`
- Modify: `src/convertor/readers/trading212_reader.py`

Background: `Trading212Stock.from_dict` reads `data.get("Currency (Result)")` into `currency_order`. Without the `Currency (Result)` CSV column, `currency_order` falls back to `Currency.USD` — which tests the fallback, not actual forwarding. Each fixture must include the column with a known value.

- [ ] **Step 1: Update `mock_csv` fixture and its test**

In `tests/readers/test_trading212_reader.py`, replace the `mock_csv` fixture:

```python
@pytest.fixture
def mock_csv(tmp_path):
    """Creates a temporary CSV file for testing."""
    csv_file = tmp_path / "test_t212.csv"
    content = (
        "Action,Ticker,Time,Total,Currency (Result)\n"
        "Deposit,,2023-01-01 10:00:00,1000.00,CZK\n"
        "Market buy,AAPL,2023-01-02 15:00:00,150.00,CZK\n"
        "Market sell,TSLA,2023-01-03 16:00:00,200.00,CZK\n"
        "Dividend (Dividend),MSFT,2023-01-04 09:00:00,5.50,CZK\n"
    )
    csv_file.write_text(content)
    return csv_file
```

Add `currency` assertion to `test_trading212_reader_parses_correctly`:

```python
    assert report.dividends[0].currency == Currency.CZK
```

Add this import at the top of the file:

```python
from convertor.currency import Currency
```

- [ ] **Step 2: Update `test_multiple_dividends`**

Replace the test function body:

```python
def test_multiple_dividends(tmp_path):
    """Test multiple dividends are aggregated correctly."""
    csv_file = tmp_path / "multi_dividends.csv"
    content = (
        "Action,Ticker,Time,Total,Currency (Result)\n"
        "Dividend (Dividend),MSFT,2023-01-04 09:00:00,5.50,CZK\n"
        "Dividend (Dividend),AAPL,2023-01-06 10:00:00,3.25,EUR\n"
        "Dividend (Dividend),GOOGL,2023-01-08 11:00:00,2.10,USD\n"
    )
    csv_file.write_text(content)

    reader = Trading212Reader()
    report = reader.read(csv_file)

    assert len(report.dividends) == 3
    assert report.dividends[0].ticker == "MSFT"
    assert report.dividends[0].amount == 5.50
    assert report.dividends[0].currency == Currency.CZK
    assert report.dividends[1].ticker == "AAPL"
    assert report.dividends[1].amount == 3.25
    assert report.dividends[1].currency == Currency.EUR
    assert report.dividends[2].ticker == "GOOGL"
    assert report.dividends[2].amount == 2.10
    assert report.dividends[2].currency == Currency.USD
```

- [ ] **Step 3: Update `test_comprehensive_all_action_types`**

Replace the CSV content and add a currency assertion:

```python
def test_comprehensive_all_action_types(tmp_path):
    """Test CSV with all supported action types."""
    csv_file = tmp_path / "comprehensive.csv"
    content = (
        "Action,Ticker,Time,Total,Currency (Result)\n"
        "Deposit,,2023-01-01 09:00:00,1000.00,CZK\n"
        "Market buy,AAPL,2023-01-02 10:00:00,100.00,CZK\n"
        "Limit buy,TSLA,2023-01-03 11:00:00,200.00,CZK\n"
        "Dividend (Dividend),MSFT,2023-01-04 12:00:00,5.50,CZK\n"
        "Market sell,GOOGL,2023-01-05 13:00:00,150.00,CZK\n"
        "Limit sell,AMZN,2023-01-06 14:00:00,250.00,CZK\n"
        "Deposit,,2023-01-07 15:00:00,500.00,CZK\n"
    )
    csv_file.write_text(content)

    reader = Trading212Reader()
    report = reader.read(csv_file)

    assert report.deposit == 1500.00
    assert len(report.buys) == 2
    assert len(report.sells) == 2
    assert len(report.dividends) == 1
    assert report.dividends[0].currency == Currency.CZK
```

- [ ] **Step 4: Update `test_dividend_without_ticker`**

Replace the CSV content and add a currency assertion:

```python
def test_dividend_without_ticker(tmp_path):
    """Test that dividends without ticker are skipped."""
    csv_file = tmp_path / "div_no_ticker.csv"
    content = (
        "Action,Ticker,Time,Total,Currency (Result)\n"
        "Dividend (Dividend),,2023-01-04 09:00:00,5.50,CZK\n"
        "Dividend (Dividend),AAPL,2023-01-05 10:00:00,3.25,EUR\n"
    )
    csv_file.write_text(content)

    reader = Trading212Reader()
    report = reader.read(csv_file)

    assert len(report.dividends) == 1
    assert report.dividends[0].ticker == "AAPL"
    assert report.dividends[0].currency == Currency.EUR
```

- [ ] **Step 5: Run tests — expect FAIL**

```bash
uv run pytest tests/readers/test_trading212_reader.py -v 2>&1 | head -30
```

Expected: tests with dividend assertions fail with `ValidationError` (reader doesn't pass currency yet)

- [ ] **Step 6: Update Trading212Reader**

In `src/convertor/readers/trading212_reader.py`, replace `_parse_dividend`:

```python
    def _parse_dividend(self, row: dict[str, str]) -> Dividend | None:
        """Parse dividend transaction from CSV row."""
        try:
            stock = Trading212Stock.from_dict(row)
            if stock.ticker and stock.time:
                return Dividend(
                    ticker=stock.ticker,
                    time=stock.time,
                    amount=stock.total_price,
                    currency=stock.currency_order,
                )
        except (ValueError, KeyError, TypeError):
            pass
        return None
```

- [ ] **Step 7: Run Trading212 tests — expect all PASS**

```bash
uv run pytest tests/readers/test_trading212_reader.py -v
```

Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add tests/readers/test_trading212_reader.py src/convertor/readers/trading212_reader.py
git commit -m "feat: thread currency through Trading212Reader dividend parsing"
```

---

## Task 3: Update XtbReader and its tests

**Files:**
- Modify: `tests/readers/test_xtb_reader.py`
- Modify: `src/convertor/readers/xtb_reader.py`

Background: `_extract_currency` slices `row[2:-4][-2]`. For a 12-column row (which openpyxl produces when any row in the sheet is 12 columns), the target is absolute index 6. The current `CURRENCY_ROW_INDEX` rows either have the wrong width or `None` at index 6, causing silent fallback to `Currency.EUR`. Using `"EUR"` at index 6 would be indistinguishable from the fallback — use `"USD"` for `mock_xlsx` and `test_multiple_transactions_same_type` so the test proves actual extraction.

- [ ] **Step 1: Fix `mock_xlsx` fixture — use USD to distinguish from fallback**

In `tests/readers/test_xtb_reader.py`, replace the `CURRENCY_ROW_INDEX` row in `mock_xlsx` (the 6th `sheet.append` call):

```python
    # Was: sheet.append([None, None, "EUR", None, None, "EUR", None])
    sheet.append([None, None, None, None, None, None, "USD", None, None, None, None, None])
```

Update `test_currency_extraction` (currently asserts `Currency.EUR`):

```python
    assert report.deposit_currency == Currency.USD
```

Add `currency` assertion to `test_xtb_reader_parses_correctly`:

```python
    assert report.dividends[0].currency == Currency.USD
```

Add `currency` assertion to `test_dividend_dates`:

```python
    assert report.dividends[0].currency == Currency.USD
```

- [ ] **Step 2: Fix `test_multiple_transactions_same_type` fixture — use USD**

Locate the CURRENCY_ROW_INDEX row in this test (currently `[None, None, "EUR", None, None, "EUR", None, None, None, None, None, None]`) and replace it:

```python
    sheet.append(
        [None, None, None, None, None, None, "USD", None, None, None, None, None]
    )
```

Add `currency` assertions for both dividends:

```python
    assert report.dividends[0].currency == Currency.USD
    assert report.dividends[1].currency == Currency.USD
```

- [ ] **Step 3: Fix `test_midnight_and_edge_dates` fixture**

Locate the CURRENCY_ROW_INDEX row in this test (currently `[None, None, "EUR", None, None, "EUR", None, None, None, None, None, None]`) and replace it:

```python
    sheet.append(
        [None, None, None, None, None, None, "EUR", None, None, None, None, None]
    )
```

Add `currency` assertion for the dividend:

```python
    assert report.dividends[0].currency == Currency.EUR
```

- [ ] **Step 4: Run XTB tests — expect FAIL**

```bash
uv run pytest tests/readers/test_xtb_reader.py -v 2>&1 | head -30
```

Expected: dividend tests fail with `ValidationError` (reader doesn't pass currency yet)

- [ ] **Step 5: Update XtbReader**

In `src/convertor/readers/xtb_reader.py`, replace `_parse_dividend` and its call site.

Replace the method signature and body (lines 82–101):

```python
    def _parse_dividend(self, values: tuple[Any, ...], currency: Currency) -> Dividend | None:
        """Parse dividend transaction."""
        try:
            time = values[self.TIME_INDEX]
            ticker = values[self.TICKER_INDEX]
            amount = values[self.AMOUNT_INDEX]

            if (
                isinstance(time, datetime)
                and ticker is not None
                and isinstance(amount, float)
            ):
                return Dividend(
                    ticker=str(ticker),
                    time=time,
                    amount=float(amount),
                    currency=currency,
                )
        except (IndexError, ValueError):
            pass
        return None
```

Replace the call site in `read()` (the `XtbAction.DIV` branch, currently line ~151):

```python
            elif action == XtbAction.DIV:
                if dividend := self._parse_dividend(values, currency):
                    report.dividends.append(dividend)
```

- [ ] **Step 6: Run XTB tests — expect all PASS**

```bash
uv run pytest tests/readers/test_xtb_reader.py -v
```

Expected: all PASS

- [ ] **Step 7: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests PASS

- [ ] **Step 8: Commit**

```bash
git add tests/readers/test_xtb_reader.py src/convertor/readers/xtb_reader.py
git commit -m "feat: thread currency through XtbReader dividend parsing"
```
