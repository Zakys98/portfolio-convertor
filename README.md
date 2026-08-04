# Portfolio Convertor

**Convert broker exports to standard format or Yahoo Finance format**

This utility bridges the gap between your brokerage data and Yahoo Finance. It converts CSV exports from supported brokers into a standard or Yahoo-compatible schema.

**Supported brokers**:
- Trading212
- XTB
- Interactive Brokers (IBKR) — stocks only

## Prerequisites

- Python: 3.13 or higher
- uv: Fast Python package manager ([Installation Guide](https://github.com/astral-sh/uv))

## Installation

Clone the repository and set up the environment using uv:
```bash
uv venv
uv sync
```

## Run

Run the script by specifying your input files and output name.
```bash
python3 src/main.py xtb.xlsx t212_export.csv --output output.json
```

Also Yahoo finance input format is supported.
```bash
python3 src/main.py xtb.xlsx t212_export.csv --output yahoo_output.csv --yahoo
```
