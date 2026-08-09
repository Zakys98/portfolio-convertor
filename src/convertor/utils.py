import re
from datetime import datetime

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


def date_to_string(date: str | datetime) -> str:
    """
    Convert a datetime object or string to a standardized string format.

    This function normalizes date values from different sources (Excel datetime
    objects, CSV strings) into a consistent string format. String values are
    passed through unchanged, assuming they're already in the correct format.

    Args:
        date: A datetime object or string representing a date/time value.

    Returns:
        A string in the format "YYYY-MM-DD HH:MM:SS". If the input is already
        a string, it is returned unchanged.

    Examples:
        >>> from datetime import datetime
        >>> date_to_string(datetime(2023, 1, 15, 10, 30, 0))
        '2023-01-15 10:30:00'
        >>> date_to_string("2023-01-15 10:30:00")
        '2023-01-15 10:30:00'

    Note:
        This function is used primarily in:
        - XtbStock.from_dict() to convert Excel datetime objects
        - Dividend field validator to normalize date inputs
    """
    if isinstance(date, datetime):
        return date.strftime(DATETIME_FORMAT)
    return date


def date_to_day(value: str | datetime) -> str:
    """
    Reduce a datetime or timestamp string to its YYYY-MM-DD day.

    Args:
        value: A datetime object, or a string in "YYYY-MM-DD HH:MM:SS" format.

    Returns:
        The day as "YYYY-MM-DD". Input that cannot be parsed degrades to its
        leading token, split on whitespace or a comma ("" for empty or
        whitespace-only input), rather than raising, because `time` values
        are not guaranteed well-formed: readers pass broker strings through
        unvalidated.

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


def parse_float(value: str | None, default: float = -1.0) -> float:
    """
    Parse a string value to float, returning a default if invalid.

    This function safely converts string representations of numbers to float
    values, with graceful handling of None, empty strings, and invalid formats.

    Args:
        value: The string to parse, or None.
        default: The value to return if parsing fails (default: -1.0).

    Returns:
        The parsed float value, or the default if parsing fails.

    Examples:
        >>> parse_float("123.45")
        123.45
        >>> parse_float("invalid", default=0.0)
        0.0
        >>> parse_float(None)
        -1.0
        >>> parse_float("")
        -1.0

    Note:
        The default value of -1.0 is used as a sentinel value in the
        Trading212Stock class to indicate missing or invalid numeric data.
    """
    if not value:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
