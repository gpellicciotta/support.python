"""Date and time parsing, formatting, and wire conversion utilities.

Provides standardized UTC ISO-8601 (yyyy-MM-dd'T'HH:mm:ss'Z') conversions
matching standard wire conventions across all services and platforms.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union

#: Standard UTC ISO-8601 wire datetime format string (``yyyy-MM-dd'T'HH:mm:ss'Z'``).
DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"


def parse_datetime(value: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """Parse a datetime string in UTC yyyy-MM-dd'T'HH:mm:ss'Z' format or normalize a datetime.

    Args:
        value: An ISO-8601 UTC date string, a datetime instance, or None.

    Returns:
        UTC-aware datetime instance, or None if the input value is None or empty.

    Raises:
        TypeError: If value is not a string, datetime instance, or None.
        ValueError: If value is a string that does not conform to DATE_FORMAT.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        return datetime.strptime(value, DATE_FORMAT).replace(tzinfo=timezone.utc)
    raise TypeError(f"Expected str or datetime, got {type(value).__name__}")


def format_datetime(value: Optional[Union[datetime, str]]) -> Optional[str]:
    """Format a datetime instance into UTC yyyy-MM-dd'T'HH:mm:ss'Z' wire string.

    Args:
        value: A datetime instance, an already formatted string, or None.

    Returns:
        Formatted UTC wire date string, or None if the input value is None.

    Raises:
        TypeError: If value is not a datetime instance, string, or None.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc)
        return value.strftime(DATE_FORMAT)
    raise TypeError(f"Expected datetime or str, got {type(value).__name__}")


def to_wire_date(value: Optional[Union[datetime, str]]) -> Optional[str]:
    """Convert a datetime instance to a wire-format UTC date string.

    Alias of :func:`format_datetime`.

    Args:
        value: A datetime instance, an already formatted string, or None.

    Returns:
        Formatted UTC wire date string, or None if the input value is None.
    """
    return format_datetime(value)


def from_wire_date(value: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """Parse a wire-format UTC date string into a datetime instance.

    Alias of :func:`parse_datetime`.

    Args:
        value: An ISO-8601 UTC date string, a datetime instance, or None.

    Returns:
        UTC-aware datetime instance, or None if the input value is None or empty.
    """
    return parse_datetime(value)


__all__ = [
    "DATE_FORMAT",
    "format_datetime",
    "from_wire_date",
    "parse_datetime",
    "to_wire_date",
]
