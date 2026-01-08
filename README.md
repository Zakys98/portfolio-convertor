# Portfolio Convertor

**Convert broker exports to standard format or Yahoo Finance format**

This utility bridges the gap between your brokerage data and Yahoo Finance. It converts CSV exports from supported brokers into a standard or Yahoo-compatible schema.

**Supported brokers**:
- Trading212
- XTB

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

Run the script by specifying your input file, desired output name, and the broker type.
```bash
python3 main.py --input t212_export.csv --output yahoo_import.csv --t212 --yahoo
```

Note:
If the output file already exists, the script will append the converted data to the end of the file instead of overwriting it.
