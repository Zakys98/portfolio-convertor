from datetime import datetime

DATETIME_FORMAT = "%Y-%m-%d"


def date_to_string(date: str | datetime) -> str:
    if isinstance(date, datetime):
        return date.strftime(DATETIME_FORMAT)
    
    if isinstance(date, str) and date:
        try:
            # Try parsing the Trading212 and older formats
            dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            return dt.strftime(DATETIME_FORMAT)
        except ValueError:
            pass
            
    return date


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
