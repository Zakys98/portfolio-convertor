# Portfolio Convertor

This tool converts broker output files to the Yahoo format.
Simply provide your broker's exported file, and the script will generate a compatible file for Yahoo Finance import.
Supported brokers input files are:
    - Trading212
    - XTB

## Requirements

- Python3


## Run

```bash
python3 main.py --input t212_export.csv --output yahoo_import.csv --t212 --yahoo
```

Note:
If the output file already exists, the script will append the converted data to the end of the file instead of overwriting it.
