# Date Column Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `date` column (`YYYY-MM-DD`, derived from `time`) to the converter's output, as the first CSV column, without changing any existing column.

**Architecture:** A `date_to_day` helper in `convertor.utils` normalizes a timestamp down to its day. `Stock` and `Dividend` each expose it through a Pydantic `@computed_field` property, so `date` cannot diverge from `time` and no reader or constructor changes. Because Pydantic serializes computed fields *last*, `ReportManager.transactions()` seeds each row dict with `date` to pull it into CSV column 1.

**Tech Stack:** Python 3.13, Pydantic v2 (`computed_field`), pytest, mypy `--strict`, ruff, uv.

**Spec:** `docs/superpowers/specs/2026-08-09-date-column-design.md`

**Baseline (verified before writing this plan):** `uv run pytest tests/ -q` → 72 passed. `uv run mypy --strict src/` → clean. Any deviation from these numbers at the start means something else is wrong; fix that first.

**A note on the commit steps:** you said you'd handle git yourself. Commit steps are included for completeness — run them or skip them as you prefer. Commit messages follow this repo's existing imperative style (`Add coverage to gitignore`, `Make IbkrReader more readable`), not conventional-commit prefixes.

---

### Task 1: `date_to_day` utility

Extract the day from a timestamp. This is the only place date parsing happens.

**Files:**
- Modify: `src/convertor/utils.py` (add `DATE_FORMAT` beside `DATETIME_FORMAT:3`; add `date_to_day` after `date_to_string`)
- Test: `tests/test_utils.py` (add a `TestDateToDay` class after `TestDateToString`, matching the existing class-per-function layout)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_utils.py`, and extend the existing import on line 10 to `from convertor.utils import DATETIME_FORMAT, date_to_day, date_to_string, parse_float`:

```python
class TestDateToDay:
    """Test suite for date_to_day function."""

    def test_timestamp_string_to_day(self):
        """Test that a full timestamp is reduced to its day."""
        assert date_to_day("2023-03-16 16:21:03") == "2023-03-16"

    def test_datetime_to_day(self):
        """Test that a datetime object is reduced to its day."""
        assert date_to_day(datetime(2023, 3, 16, 16, 21, 3)) == "2023-03-16"

    def test_date_only_string_passthrough(self):
        """Test that an already-day-shaped string survives the fallback path."""
        assert date_to_day("2023-03-16") == "2023-03-16"

    def test_empty_string(self):
        """Test that empty input yields empty output rather than raising."""
        assert date_to_day("") == ""

    def test_malformed_string_returns_leading_token(self):
        """Test the best-effort fallback for unparseable input.

        Reachable in practice: IbkrReader._parse_datetime falls back to the raw
        string when strptime fails, and Trading212Stock.from_dict assigns time
        straight from the CSV. Export must not crash on bad broker data.
        """
        assert date_to_day("not a date") == "not"

    def test_midnight_timestamp(self):
        """Test that a midnight timestamp keeps its own day."""
        assert date_to_day("2024-02-29 00:00:00") == "2024-02-29"

    def test_ibkr_comma_format_fallback(self):
        """IbkrReader passes its comma-form timestamp through raw when strptime fails."""
        assert date_to_day("2023-03-16, 16:21") == "2023-03-16"

    def test_surrounding_whitespace(self):
        """Trading212 assigns time straight from DictReader, which does not strip."""
        assert date_to_day(" 2023-03-16 16:21:03 ") == "2023-03-16"
```

The last two cases are the ones that actually flow through this code in production, and
they are why the fallback tokenizes on whitespace *or* comma rather than on `" "` alone:

- `ibkr_reader.py:12` defines `IBKR_DATETIME_FORMAT = "%Y-%m-%d, %H:%M:%S"`, and
  `_parse_datetime` returns `value.strip()` unchanged when `strptime` fails — so a
  comma-form timestamp arrives here intact. A naive `split(" ")[0]` yields
  `"2023-03-16,"`, a non-date that also forces CSV quoting in the new column.
- `Trading212Stock.from_dict` assigns `time` straight from `csv.DictReader`, which
  defaults to `skipinitialspace=False`. A naive `split(" ")[0]` turns a *well-formed*
  timestamp with one stray leading space into `""` — silent loss of a recoverable value.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_utils.py::TestDateToDay -v`
Expected: collection error — `ImportError: cannot import name 'date_to_day' from 'convertor.utils'`.

- [ ] **Step 3: Write the implementation**

In `src/convertor/utils.py`, add the constant next to the existing one:

```python
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
```

And add this function immediately after `date_to_string`:

```python
def date_to_day(value: str | datetime) -> str:
    """
    Reduce a datetime or timestamp string to its YYYY-MM-DD day.

    Args:
        value: A datetime object, or a string in "YYYY-MM-DD HH:MM:SS" format.

    Returns:
        The day as "YYYY-MM-DD". Input that cannot be parsed degrades to its
        leading whitespace- or comma-delimited token ("" for empty input)
        rather than raising, because `time` values are not guaranteed
        well-formed: readers pass broker strings through unvalidated.

    Examples:
        >>> from datetime import datetime
        >>> date_to_day("2023-03-16 16:21:03")
        '2023-03-16'
        >>> date_to_day(datetime(2023, 3, 16, 16, 21, 3))
        '2023-03-16'
        >>> date_to_day("")
        ''
    """
    text = date_to_string(value)
    try:
        return datetime.strptime(text, DATETIME_FORMAT).strftime(DATE_FORMAT)
    except ValueError:
        return re.split(r"[\s,]", text.strip(), maxsplit=1)[0]
```

This needs `import re` at the top of the module.

Parse-and-reformat via `strptime`/`strftime` is deliberate rather than a `text[:10]`
slice: it *validates* the happy path, and it normalizes sloppy padding for free
(`"2023-3-16 16:21:03"` → `"2023-03-16"`, where a slice would emit `"2023-3-16 "`).

The `str | datetime` parameter type is required, not incidental: `Dividend.time` is typed `str | datetime`, so a `str`-only signature fails `mypy --strict` at that call site in Task 2. Delegating to `date_to_string` normalizes both inputs in one place.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_utils.py -v`
Expected: PASS — the 8 new tests plus all pre-existing `test_utils.py` tests.

Also refresh the module docstring at `tests/test_utils.py:4`, which claims the file
"Tests cover date_to_string and parse_float functions" — there are now three classes.

- [ ] **Step 5: Type-check**

Run: `uv run mypy --strict src/`
Expected: `Success: no issues found in 18 source files`

- [ ] **Step 6: Commit**

```bash
git add src/convertor/utils.py tests/test_utils.py
git commit -m "Add date_to_day util"
```

---

### Task 2: `date` on `Dividend`

Do `Dividend` before `Stock`: it is the case that exercises `date_to_day`'s `str | datetime` signature, so a wrong signature fails here immediately rather than silently later.

**Files:**
- Modify: `src/convertor/stocks/dividend.py`
- Test: `tests/test_dividend.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_dividend.py` (add `from datetime import datetime` to its imports):

```python
def test_dividend_date_from_string_time():
    d = Dividend(ticker="MSFT", time="2023-01-04 09:00:00", amount=5.50, currency=Currency.EUR)
    assert d.date == "2023-01-04"


def test_dividend_date_from_datetime_time():
    d = Dividend(ticker="JPM", time=datetime(2023, 2, 1, 15, 5, 55), amount=37.13, currency=Currency.CZK)
    assert d.date == "2023-02-01"


def test_dividend_date_is_serialized():
    d = Dividend(ticker="JPM", time="2023-02-01 15:05:55", amount=37.13, currency=Currency.CZK)
    assert d.model_dump()["date"] == "2023-02-01"


def test_dividend_date_is_not_settable():
    """date is computed from time, so it must not be independently assignable."""
    d = Dividend(
        ticker="JPM", time="2023-02-01 15:05:55", amount=37.13,
        currency=Currency.CZK, date="1999-12-31",
    )
    assert d.date == "2023-02-01"
```

The last test pins the reason a computed field was chosen over a stored one. Pydantic ignores unknown keyword arguments by default, so `date="1999-12-31"` is discarded rather than raising.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_dividend.py -v`
Expected: 4 failures, `AttributeError: 'Dividend' object has no attribute 'date'` (and `KeyError: 'date'` for the serialization test). The 2 pre-existing tests still pass.

- [ ] **Step 3: Write the implementation**

In `src/convertor/stocks/dividend.py`, extend the imports and add the property:

```python
from pydantic import BaseModel, computed_field, field_validator
from datetime import datetime

from convertor.currency import Currency
from convertor.utils import date_to_day, date_to_string


class Dividend(BaseModel):
    ticker: str
    time: str | datetime  # datetime type is just for input and it is converted to str
    amount: float
    currency: Currency

    # mypy does not support decorators stacked on @property (prop-decorator);
    # the Pydantic plugin does not suppress it either. Pydantic itself handles
    # this pattern correctly at runtime.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> str:
        return date_to_day(self.time)

    @field_validator("time", mode="before")
    @classmethod
    def format_date(cls, value: str | datetime) -> str:
        return date_to_string(value)
```

Decorator order matters: `@computed_field` goes *above* `@property`. Reversed, Pydantic will not pick it up.

**The `# type: ignore[prop-decorator]` is mandatory, not optional.** CI runs
`mypy --strict`, and mypy refuses any decorator stacked on `@property`. This is a
general mypy limitation, not a Pydantic or version-pin problem — verified: adding
`[tool.mypy] plugins = ["pydantic.mypy"]` loads the plugin cleanly and produces
byte-identical output, so plugin config is *not* the remedy. Do not add a
`[tool.mypy]` section and do not bump pins. The repo already uses this exact
pattern at `src/main.py:93`.

Keep the explanatory comment so the ignore does not read as stray. `--strict`
enables `warn_unused_ignores`, so if mypy ever fixes `prop-decorator` the ignore
will start erroring — the signal we want.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_dividend.py -v`
Expected: PASS, 6 tests.

- [ ] **Step 5: Type-check**

Run: `uv run mypy --strict src/`
Expected: `Success`. If it reports `Argument 1 to "date_to_day" has incompatible type "str | datetime"`, Task 1's signature was written as `str` only — fix it there, not here.

- [ ] **Step 6: Commit**

```bash
git add src/convertor/stocks/dividend.py tests/test_dividend.py
git commit -m "Add date field to Dividend"
```

---

### Task 3: `date` on `Stock`

**Files:**
- Modify: `src/convertor/stocks/stock.py`
- Create: `tests/test_stock.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_stock.py`. The three subclass cases confirm inheritance — `XtbStock`, `Trading212Stock`, and `IbkrStock` must gain `date` with no changes of their own. All constructor calls below were verified against the real models.

```python
"""Unit tests for the Stock model's computed date field."""

from datetime import datetime

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

    ReportManager relies on this to know date needs explicit repositioning
    for the CSV. If this ever changes, the seed in transactions() is redundant.
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


def test_to_yahoo_unaffected():
    """The Yahoo export has its own fixed fieldnames and must not gain date."""
    assert "date" not in _stock("2023-03-16 16:21:03").to_yahoo()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_stock.py -v`
Expected: 7 failures on the missing `date` attribute/key. `test_to_yahoo_unaffected` passes already — that is correct, it is a regression guard.

- [ ] **Step 3: Write the implementation**

In `src/convertor/stocks/stock.py`:

```python
from pydantic import BaseModel, computed_field

from convertor.currency import Currency
from convertor.constants import Yahoo
from convertor.utils import date_to_day


class Stock(BaseModel):
    ticker: str
    time: str
    quantity: float
    share_price: float
    currency_main: Currency
    total_price: float

    # mypy does not support decorators stacked on @property (prop-decorator);
    # the Pydantic plugin does not suppress it either. Pydantic itself handles
    # this pattern correctly at runtime.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> str:
        return date_to_day(self.time)

    def to_yahoo(self) -> dict[str, str | float | int]:
        return {
            Yahoo.SYMBOL: self.ticker,
            Yahoo.TRADE_DATE: self.time,
            Yahoo.QUANTITY: self.quantity,
            Yahoo.PURCHASE_PRICE: self.share_price,
            Yahoo.COMMISSION: 0,
        }
```

`to_yahoo` is untouched — it builds its own dict against the fixed `Yahoo` fieldname list.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_stock.py -v`
Expected: PASS, 8 tests.

- [ ] **Step 5: Confirm no reader test regressed**

Run: `uv run pytest tests/ -q`
Expected: 92 passed (72 baseline + 8 from Task 1 + 4 from Task 2 + 8 from Task 3). Exact total is not the point — **zero failures** is. A computed field adds no constructor argument, so no existing reader test should need editing. If one fails, stop and read it: it likely asserts an exact `model_dump()` dict, and that is a real finding worth reporting, not something to paper over.

- [ ] **Step 6: Type-check and commit**

```bash
uv run mypy --strict src/
git add src/convertor/stocks/stock.py tests/test_stock.py
git commit -m "Add date field to Stock"
```

---

### Task 4: `date` as the first CSV column

`Stock` and `Dividend` now serialize `date` last. This task moves it to column 1.

**Files:**
- Modify: `src/convertor/report_manager.py:20-33` (`transactions`)
- Create: `tests/test_report_manager.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_report_manager.py`. Note `Report[Stock]` — `Report` is generic over `T: Stock`, and the parametrized form is what `ReportManager.reports` expects.

```python
"""Unit tests for ReportManager output, focused on the date column."""

import csv
import json

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


def test_transactions_put_date_first_and_type_second():
    for row in _manager().transactions():
        assert list(row)[:2] == ["date", "type"]


def test_transactions_have_no_duplicate_date():
    """The dict-union seed must not produce two date entries."""
    for row in _manager().transactions():
        assert list(row).count("date") == 1


def test_transaction_date_matches_its_time():
    for row in _manager().transactions():
        assert row["date"] == row["time"][:10]


def test_csv_header_starts_with_date(tmp_path):
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    header = output.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header[:2] == ["date", "type"]


def test_csv_keeps_all_existing_columns(tmp_path):
    """date is additive: no pre-existing column may be dropped or renamed."""
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    header = output.read_text(encoding="utf-8").splitlines()[0].split(",")
    expected = {
        "type", "ticker", "time", "quantity", "share_price",
        "currency_main", "total_price", "amount", "currency",
    }
    assert expected.issubset(set(header))


def test_csv_rows_carry_date(tmp_path):
    output = tmp_path / "out.csv"
    _manager().write_csv(output)
    with output.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert [row["date"] for row in rows] == ["2023-02-01", "2023-03-16", "2023-04-28"]


def test_json_includes_date_for_every_kind(tmp_path):
    output = tmp_path / "out.json"
    _manager().write_json(output)
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["buys"][0]["date"] == "2023-03-16"
    assert data["sells"][0]["date"] == "2023-04-28"
    assert data["dividends"][0]["date"] == "2023-02-01"


def test_empty_report_still_writes_empty_csv(tmp_path):
    output = tmp_path / "out.csv"
    ReportManager().write_csv(output)
    assert output.read_text(encoding="utf-8") == ""
```

Two deliberate choices here:

`test_csv_rows_carry_date` expects dividend-first ordering because `transactions()` sorts by `time`, and the dividend is the earliest at `2023-02-01`.

`test_csv_keeps_all_existing_columns` asserts a **subset**, not an exact header. `write_csv` builds `fieldnames` as a union across rows *after* sorting, so the order of columns after `date` depends on whether the earliest transaction is a dividend or a buy. That is pre-existing behavior this change does not touch; asserting an exact header string would make the test brittle for reasons unrelated to `date`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_report_manager.py -v`
Expected: exactly 2 failures — `test_transactions_put_date_first_and_type_second` and `test_csv_header_starts_with_date`. `date` currently serializes last, so `list(row)[:2] == ["type", "ticker"]`.

The other 6 already pass, and that is intended: after Tasks 2 and 3 `date` exists and is correct, it is merely in the wrong position. They are regression guards for this task, not drivers of it. If any of those 6 fails here, something in Task 2 or 3 is wrong — go back rather than editing `report_manager.py`.

- [ ] **Step 3: Write the implementation**

Replace the loop body in `transactions()` in `src/convertor/report_manager.py`:

```python
            for item in items:
                dump = item.model_dump()
                transactions.append({"date": dump["date"], "type": type_} | dump)
```

A dict union keeps the first occurrence's key *position* and the last occurrence's *value*. Both are `dump["date"]`, so `date` lands first with no duplicate column and no way for the seed to drift from the serialized value.

`write_csv` derives `fieldnames` from the row keys, so it picks the new leading column up with no change of its own.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_report_manager.py -v`
Expected: PASS, 8 tests.

- [ ] **Step 5: Commit**

```bash
git add src/convertor/report_manager.py tests/test_report_manager.py
git commit -m "Put date first in CSV output"
```

---

### Task 5: Full verification

- [ ] **Step 1: Run the full suite with coverage, exactly as CI does**

Run: `uv run pytest tests/ -v --cov=src/convertor --cov-report=term-missing --cov-fail-under=75`
Expected: all tests pass, coverage gate met. Coverage should *rise* — `report_manager.py` had no direct test coverage before Task 4.

- [ ] **Step 2: Type-check, exactly as CI does**

Run: `uv run mypy --strict src/`
Expected: `Success: no issues found in 18 source files`

- [ ] **Step 3: Lint, exactly as CI does**

Run: `uvx ruff check src/ tests/ && uvx ruff format --check src/ tests/`
Expected: no findings. (`ruff` is not in the dependency group — CI uses `astral-sh/ruff-action`. `uvx` fetches it, so this step needs network access; skip it if offline and note that you did.)

- [ ] **Step 4: Verify against real broker data end-to-end**

Run:
```bash
uv run python src/main.py inputs/from_2023.csv inputs/from_2024.csv inputs/xtb_jiri.xlsx -o /tmp/verify.csv
head -3 /tmp/verify.csv
```
Expected: the header begins `date,type,ticker,time,...` and each row's `date` is the day portion of its `time`. This is the check that the feature actually works on real exports, not just on fixtures.

Then confirm the JSON path and that `--yahoo` is unchanged:
```bash
uv run python src/main.py inputs/from_2023.csv -o /tmp/verify.json --format json
uv run python src/main.py inputs/from_2023.csv -o /tmp/verify_yahoo.csv --yahoo
head -1 /tmp/verify_yahoo.csv
```
Expected: `/tmp/verify.json` objects each carry a `date` key; the Yahoo header is exactly `Symbol,Trade Date,Quantity,Purchase Price,Commission` with no `date`.

Note: `inputs/` files and the tracked `output.csv` are real personal data. Write verification output to `/tmp`, and do not commit regenerated `output.csv`.

- [ ] **Step 5: Update the README if needed**

Read `README.md`. It documents the run commands but does not enumerate output columns, so it most likely needs no change. Confirm rather than assume; if it does list columns, add `date`.

---

## Out of Scope

Per the spec, do not do these here even if tempting:

- Renaming `share_price` → `price` or `currency_main` → `currency`
- Adding `fees`, `notes`, or `isin` columns (the Trading212 reader drops the export's `ISIN` and `Notes`; IBKR trades carry `Comm/Fee`)
- Suppressing `DIVIDEND` rows
- Adding `GBp` to the `Currency` enum
- Changing the `--yahoo` output
- Alternative date renderings (`YYYY/M/D`, `M/D/YYYY`)
