"""
Unit tests for utility functions in convertor.utils module.

Tests cover date_to_string and parse_float functions with various
edge cases and input scenarios.
"""

from datetime import datetime

from convertor.utils import DATETIME_FORMAT, date_to_string, parse_float


class TestDateToString:
    """Test suite for date_to_string function."""

    def test_datetime_to_string_conversion(self):
        """Test conversion of datetime object to string format."""
        dt = datetime(2023, 1, 15, 10, 30, 45)
        result = date_to_string(dt)
        assert result == "2023-01-15 10:30:45"
        assert isinstance(result, str)

    def test_string_passthrough(self):
        """Test that string values are passed through unchanged."""
        date_str = "2023-01-15 10:30:45"
        result = date_to_string(date_str)
        assert result == date_str
        assert result is date_str  # Should be the same object

    def test_datetime_at_midnight(self):
        """Test datetime conversion at midnight (00:00:00)."""
        dt = datetime(2023, 6, 1, 0, 0, 0)
        result = date_to_string(dt)
        assert result == "2023-06-01 00:00:00"

    def test_datetime_with_various_times(self):
        """Test datetime conversion with different time values."""
        test_cases = [
            (datetime(2023, 12, 31, 23, 59, 59), "2023-12-31 23:59:59"),
            (datetime(2023, 1, 1, 0, 0, 1), "2023-01-01 00:00:01"),
            (datetime(2023, 6, 15, 12, 0, 0), "2023-06-15 12:00:00"),
        ]
        for dt, expected in test_cases:
            assert date_to_string(dt) == expected

    def test_leap_year_date(self):
        """Test datetime conversion with leap year date."""
        dt = datetime(2024, 2, 29, 15, 30, 0)  # 2024 is a leap year
        result = date_to_string(dt)
        assert result == "2024-02-29 15:30:00"

    def test_year_boundary_dates(self):
        """Test dates at year boundaries."""
        # Last day of year
        dt_end = datetime(2023, 12, 31, 23, 59, 59)
        assert date_to_string(dt_end) == "2023-12-31 23:59:59"

        # First day of year
        dt_start = datetime(2024, 1, 1, 0, 0, 0)
        assert date_to_string(dt_start) == "2024-01-01 00:00:00"

    def test_format_constant_used(self):
        """Test that the function uses the DATETIME_FORMAT constant."""
        dt = datetime(2023, 5, 10, 14, 25, 30)
        result = date_to_string(dt)
        # Verify result matches the format defined in DATETIME_FORMAT
        assert result == dt.strftime(DATETIME_FORMAT)

    def test_different_string_formats_passthrough(self):
        """Test that various string formats are passed through unchanged."""
        test_strings = [
            "2023-01-15 10:30:45",
            "2023/01/15 10:30:45",  # Different separator
            "15-01-2023",  # Different order
            "not a date",  # Invalid format
            "",  # Empty string
        ]
        for date_str in test_strings:
            assert date_to_string(date_str) == date_str


class TestParseFloat:
    """Test suite for parse_float function."""

    def test_parse_valid_float_string(self):
        """Test parsing valid float string."""
        result = parse_float("123.45")
        assert result == 123.45
        assert isinstance(result, float)

    def test_parse_valid_integer_string(self):
        """Test parsing integer string as float."""
        result = parse_float("100")
        assert result == 100.0
        assert isinstance(result, float)

    def test_parse_negative_float(self):
        """Test parsing negative float."""
        result = parse_float("-45.67")
        assert result == -45.67

    def test_parse_zero(self):
        """Test parsing zero."""
        assert parse_float("0") == 0.0
        assert parse_float("0.0") == 0.0

    def test_parse_invalid_string_returns_default(self):
        """Test that invalid string returns default value."""
        result = parse_float("invalid")
        assert result == -1.0

    def test_parse_none_returns_default(self):
        """Test that None returns default value."""
        result = parse_float(None)
        assert result == -1.0

    def test_parse_empty_string_returns_default(self):
        """Test that empty string returns default value."""
        result = parse_float("")
        assert result == -1.0

    def test_parse_whitespace_returns_default(self):
        """Test that whitespace-only string returns default value."""
        result = parse_float("   ")
        assert result == -1.0

    def test_parse_with_custom_default(self):
        """Test parsing with custom default value."""
        result = parse_float("invalid", default=0.0)
        assert result == 0.0

        result = parse_float(None, default=999.9)
        assert result == 999.9

    def test_parse_scientific_notation(self):
        """Test parsing scientific notation."""
        result = parse_float("1.5e2")
        assert result == 150.0

        result = parse_float("3.14e-2")
        assert result == 0.0314

    def test_parse_very_large_number(self):
        """Test parsing very large number."""
        result = parse_float("999999999999.99")
        assert result == 999999999999.99

    def test_parse_very_small_number(self):
        """Test parsing very small number."""
        result = parse_float("0.000000001")
        assert result == 0.000000001

    def test_parse_with_leading_trailing_spaces(self):
        """Test parsing string with leading/trailing spaces."""
        # Python's float() handles this, so it should work
        result = parse_float("  123.45  ")
        assert result == 123.45

    def test_parse_string_with_multiple_dots(self):
        """Test parsing string with invalid format (multiple dots)."""
        result = parse_float("123.45.67")
        assert result == -1.0

    def test_parse_currency_like_string(self):
        """Test parsing string with currency symbols (should fail)."""
        result = parse_float("$123.45")
        assert result == -1.0

    def test_parse_with_commas(self):
        """Test parsing string with commas (should fail)."""
        result = parse_float("1,234.56")
        assert result == -1.0

    def test_default_parameter_default_value(self):
        """Test that default parameter defaults to -1.0."""
        # This tests the function signature
        result = parse_float("invalid")
        assert result == -1.0

    def test_parse_infinity(self):
        """Test parsing infinity values."""
        result = parse_float("inf")
        assert result == float("inf")

        result = parse_float("-inf")
        assert result == float("-inf")

    def test_parse_nan(self):
        """Test parsing NaN."""
        result = parse_float("nan")
        assert result != result  # NaN is not equal to itself
