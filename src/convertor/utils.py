from datetime import datetime


def date_to_string(date: str | datetime) -> str:
    if isinstance(date, datetime):
        return date.strftime("%Y-%m-%d %H:%M:%S")
    return date
