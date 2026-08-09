# Date Column Design

**Date:** 2026-08-09
**Status:** Superseded in part -- see [Amendment](#amendment-strict-importer-whitelist)

> **Amendment summary.** This spec was written on the assumption that `date` had to
> be *added* to the existing wide CSV. The importer turned out to validate its header
> strictly, rejecting all eight of our internal columns, so the CSV was reduced to the
> importer's whitelist instead. The `date` computed fields below are unchanged and
> still correct; the `ReportManager` dict-union seed was removed. Details at the end.

## Problem

The target import format expects a `date` column in `YYYY-MM-DD` form as its first
column. The current output has no `date` column at all — only `time`, a full
`YYYY-MM-DD HH:MM:SS` timestamp:

```
type,ticker,time,quantity,share_price,currency_main,total_price,name,currency_order,exchange_rate,amount,currency
BUY,DVN,2023-03-16 16:21:03,1.0,45.17,USD,1025.11,Devon Energy,CZK,0.04412985,,
```

## Decision

Add `date` as a computed field on `Stock` and `Dividend`, derived from `time`.
`date` becomes the first CSV column. Every existing column is preserved,
including `time`.

Scope is deliberately narrow: no columns are renamed, dropped, or reordered
beyond prepending `date`. The wider gaps between the current output and the
target format (`price` vs `share_price`, `currency` vs `currency_main`, and the
absent `fees`, `notes`, and `isin` columns) are out of scope — see
[Out of Scope](#out-of-scope).

## Approach

`date` is a `@computed_field` property, not a stored field. It is a pure
function of `time`, so it should not be independently settable — a stored field
could be passed a value that contradicts `time`. A computed field also means no
reader, constructor, or existing test needs to change to supply it.

The rejected alternative was a regular `date: str` field populated in
`model_post_init`. It would serialize in declaration order (so it could sit
first without help in `report_manager.py`), but it widens every model
constructor and makes `date`/`time` divergence representable.

## Utility

`src/convertor/utils.py` gains a `DATE_FORMAT` constant and a `date_to_day`
helper beside the existing `date_to_string`:

```python
DATE_FORMAT = "%Y-%m-%d"


def date_to_day(value: str | datetime) -> str:
    """Extract the YYYY-MM-DD day from a datetime or "YYYY-MM-DD HH:MM:SS" string."""
    text = date_to_string(value)
    try:
        return datetime.strptime(text, DATETIME_FORMAT).strftime(DATE_FORMAT)
    except ValueError:
        return re.split(r"[\s,]", text.strip(), maxsplit=1)[0]
```

The `str | datetime` parameter type matters for mypy: `Dividend.time` is typed
`str | datetime`, so a `str`-only signature would fail type checking at that call
site even though the field validator normalizes the value at runtime. Delegating
to `date_to_string` handles both inputs in one place.

The `ValueError` fallback also matters. `time` is not guaranteed to be a
well-formed timestamp:

- `date_to_string` passes `str` inputs through unvalidated (`utils.py`).
- `Trading212Stock.from_dict` assigns `time` straight from the CSV column,
  defaulting to `""` when absent (`trading212_stock.py`).
- `IbkrReader._parse_datetime` and `_parse_date` fall back to `value.strip()`
  when `strptime` fails (`ibkr_reader.py`).

Rather than raising mid-export, the helper degrades to a best-effort prefix:
`"2023-03-16"` for a date-only input, `""` for empty input, and the leading
whitespace- or comma-delimited token otherwise.

The fallback strips and splits on comma as well as whitespace, which a plain
`text.split(" ")[0]` would not. Both cases are reachable, not hypothetical:

- `ibkr_reader.py` uses `IBKR_DATETIME_FORMAT = "%Y-%m-%d, %H:%M:%S"` and returns
  `value.strip()` unchanged when `strptime` fails, so a comma-form timestamp arrives
  intact. Splitting on `" "` alone yields `"2023-03-16,"` — not a date, and comma-bearing,
  so it would force quoting in the very column this change adds.
- `Trading212Stock.from_dict` reads `time` straight from `csv.DictReader`, which defaults
  to `skipinitialspace=False`. Splitting on `" "` alone turns a *well-formed* timestamp
  carrying one stray leading space into `""` — silent loss of a recoverable value, which
  is worse than the degraded-but-informative result this fallback is meant to give.

## Data Model

The same computed field is added to both models. `stock.py` and `dividend.py`
each need `computed_field` imported from `pydantic` and `date_to_day` imported
from `convertor.utils`.

```python
class Stock(BaseModel):
    ticker: str
    time: str
    quantity: float
    share_price: float
    currency_main: Currency
    total_price: float

    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> str:
        return date_to_day(self.time)
```

```python
class Dividend(BaseModel):
    ticker: str
    time: str | datetime
    amount: float
    currency: Currency

    @computed_field  # type: ignore[prop-decorator]
    @property
    def date(self) -> str:
        return date_to_day(self.time)
```

`XtbStock`, `Trading212Stock`, and `IbkrStock` inherit the field with no
changes. `to_yahoo` is unaffected.

## Output

Pydantic serializes computed fields after declared ones, so `model_dump()`
places `date` last. To put it first in the CSV, `ReportManager.transactions()`
seeds each row dict with it:

```python
for item in items:
    dump = item.model_dump()
    transactions.append({"date": dump["date"], "type": type_} | dump)
```

A dict union keeps the first occurrence's key *position* and the last
occurrence's *value*. Both are `dump["date"]` here, so there is no duplicate
column and no way for the two to diverge.

`write_csv` derives `fieldnames` from the row keys, so it picks up the new
leading column with no further change:

```
date,type,ticker,time,quantity,share_price,currency_main,total_price,name,currency_order,exchange_rate,amount,currency
2023-03-16,BUY,DVN,2023-03-16 16:21:03,1.0,45.17,USD,1025.11,Devon Energy,CZK,0.04412985,,
```

`write_json` calls `model_dump()` directly, so each buy, sell, and dividend
object gains a trailing `"date"` key:

```json
{"ticker": "JPM", "time": "2023-02-01 15:05:55", "amount": 37.13, "currency": "CZK", "date": "2023-02-01"}
```

Column position is meaningless in JSON, so no ordering work is needed there.

The `--yahoo` output is unchanged. It builds its rows through `Stock.to_yahoo()`
against the fixed `Yahoo` fieldname list and already carries a `Trade Date`
column.

Sorting is unchanged: `_filter_by_time` continues to sort on `time`, which is
strictly more precise than `date`.

## Test Changes

Test-driven: each test below is written and observed failing before the
corresponding implementation.

No existing test references `write_csv`, `write_json`, `transactions()`, or
`model_dump`, and the computed field requires no constructor changes, so no
existing test needs editing. All changes are additions.

**`tests/test_utils.py`** — `date_to_day` cases:
- `"2023-03-16 16:21:03"` → `"2023-03-16"`
- `datetime(2023, 3, 16, 16, 21, 3)` → `"2023-03-16"`
- `"2023-03-16"` (date-only, hits the fallback) → `"2023-03-16"`
- `""` → `""`
- `"not a date"` → `"not"` (documents the best-effort fallback)

**`tests/test_dividend.py`** — `date` derived correctly from both a `str` and a
`datetime` `time` input.

**`tests/test_stock.py`** (new) — `date` present and correct on `Stock`,
`XtbStock`, `Trading212Stock`, and `IbkrStock`, confirming inheritance.

**`tests/test_report_manager.py`** (new) — `ReportManager` currently has no
direct test coverage, so this file holds the regression protection for the
output contract:
- `transactions()` puts `date` first and `type` second in key order
- `write_csv` header is `date,type,...` with all pre-existing columns retained
- a CSV row's `date` matches the day portion of its `time`
- `write_json` includes `date` on buys, sells, and dividends
- the empty-report case still writes an empty file

## Amendment: strict importer whitelist

The importer rejected the output with:

```
Unknown CSV columns: time, share_price, currency_main, total_price, name,
currency_order, exchange_rate, amount. Valid columns: date, type, ticker,
quantity, price, currency, fees, notes, tocurrency, toamount, isin
```

So the column guide was an exact whitelist, not a minimum, and the additive approach
above could not work. Revised decisions:

- **The CSV is now exactly the importer's columns**: `date, type, ticker, quantity,
  price, currency, fees, notes, isin`, declared by a `Standard` StrEnum in
  `constants.py` mirroring the existing `Yahoo` enum. `tocurrency`/`toamount` are
  omitted; they appear to describe currency-conversion rows, which this tool does not
  emit.
- **`Stock.to_standard(type_)`** builds one row, mirroring `to_yahoo()`. `type_` is a
  parameter because only the caller knows buy from sell.
- **`write_csv` passes `Standard.to_list()` to `DictWriter`**, so column order is
  declared. This made the dict-union seed unnecessary, and `transactions()` — which
  nothing else used — was deleted along with it.
- **Only buys and sells are emitted.** The guide states dividends and splits are
  handled automatically, and `DIVIDEND` is not an accepted `type`. `_trades()`
  replaces `transactions()`, returning `(type, Stock)` pairs sorted by `time`.
- **`fees`, `notes` and `isin` are emitted empty.** All three are optional. No reader
  captures them yet.
- **An empty report now writes a header-only file** rather than an empty one, matching
  `yahoo_output` and remaining valid for import.
- **JSON output is unchanged** and keeps the full detail, including dividends and the
  deposit totals. It is the debugging view.

Verified against all five real broker exports: 886 buy/sell rows, header exactly the
nine columns, no unknown columns, no missing required values, sorted oldest-first.

## Known defects found but not fixed

Both are pre-existing and were deliberately left alone:

- `T212Action` in `trading212_reader.py` lists only `Dividend (Dividend)`. The real
  exports also contain `Dividend (Ordinary)`, `Dividend (Dividends paid by us
  corporations)`, `Dividend (Dividends paid by foreign corporations)`, `Dividend (Tax
  exempted)` and `Dividend (Dividend manufactured payment)`. Twelve dividend rows are
  silently dropped by the `except ValueError: continue` branch.
- 43 `Currency conversion` rows are dropped entirely. These are the likely source for
  the importer's `tocurrency`/`toamount` columns.
- `to_yahoo` maps `Yahoo.TRADE_DATE` to `self.time`, a full timestamp, where Yahoo
  wants a day. Now a one-word fix (`self.date`) but out of scope.

## Out of Scope

- Renaming `share_price` → `price` or `currency_main` → `currency`
- Adding `fees`, `notes`, or `isin` columns. The Trading212 export carries `ISIN`
  and `Notes` columns that the reader currently drops; IBKR trades carry
  `Comm/Fee`; XTB books fees as separate `Sec Fee` transactions. Capturing any of
  these is a separate change.
- Suppressing `DIVIDEND` rows, which the target importer derives on its own
- Adding `GBp` to the `Currency` enum for UK listings
- Changing the `--yahoo` output format
- Alternative date renderings (`YYYY/M/D`, `M/D/YYYY`) that the target format
  also accepts
