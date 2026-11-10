"""Date and time parsing, formatting, and wire conversion utilities.

Provides standardized UTC ISO-8601 (yyyy-MM-dd'T'HH:mm:ss'Z') conversions
matching standard wire conventions across all services and platforms.
Parsing also accepts millisecond (or finer) instants and explicit UTC offsets,
and date-only values use ``YYYY-MM-DD``.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re
from typing import Optional, Union

#: Standard UTC ISO-8601 wire datetime format string (``yyyy-MM-dd'T'HH:mm:ss'Z'``).
DATE_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"

# An instant with whole seconds or 1-6 fractional digits, ending in 'Z' or a '+HH:MM'/'-HH:MM' offset.
_INSTANT_PATTERN = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(?:(Z)|([+-])(\d{2}):(\d{2}))",
    re.ASCII,
)

# A date-only value in YYYY-MM-DD form.
_DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})", re.ASCII)


def _parse_instant(value: str) -> datetime:
    """Parse an ISO-8601 instant string into a UTC-aware datetime, raising ValueError when it is malformed."""
    match = _INSTANT_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"Invalid instant '{value}'; expected yyyy-MM-dd'T'HH:mm:ss[.SSS] with 'Z' or a +HH:MM offset")
    year, month, day, hour, minute, second, fraction, zulu, sign, offset_hours, offset_minutes = match.groups()
    zone = timezone.utc
    if not zulu:
        hours, minutes = int(offset_hours), int(offset_minutes)
        if hours > 23 or minutes > 59:
            raise ValueError(f"Invalid UTC offset in instant '{value}'")
        delta = timedelta(hours=hours, minutes=minutes)
        zone = timezone(-delta if sign == "-" else delta)
    microsecond = int(fraction.ljust(6, "0")) if fraction else 0
    parsed = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), microsecond, tzinfo=zone)
    try:
        return parsed.astimezone(timezone.utc)
    except OverflowError as exc:
        raise ValueError(f"Instant '{value}' falls outside the supported date range in UTC") from exc


def parse_datetime(value: Optional[Union[str, datetime]]) -> Optional[datetime]:
    """Parse an ISO-8601 instant string or normalize a datetime to UTC.

    Strings must carry a date, a time with whole seconds or 1 to 6 fractional digits, and a zone:
    ``Z`` or a ``+HH:MM``/``-HH:MM`` offset, e.g. ``2026-11-06T10:15:30.123Z`` or ``2026-11-08T18:00:00+01:00``.

    Args:
        value: An ISO-8601 instant string, a datetime instance, or None.

    Returns:
        UTC-aware datetime instance, or None if the input value is None or empty.

    Raises:
        TypeError: If value is not a string, datetime instance, or None.
        ValueError: If value is a string that is not a valid instant with a zone.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        return _parse_instant(value)
    raise TypeError(f"Expected str or datetime, got {type(value).__name__}")


def format_datetime(value: Optional[Union[datetime, str]], *, millis: bool = False) -> Optional[str]:
    """Format a datetime instance into a UTC yyyy-MM-dd'T'HH:mm:ss'Z' wire string.

    Args:
        value: A datetime instance, an already formatted string, or None.
        millis: If True, emit exactly three fractional digits (``yyyy-MM-dd'T'HH:mm:ss.SSS'Z'``) for datetime
            inputs, truncating finer precision; string inputs are always returned unchanged.

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
        if millis:
            return f"{value.strftime('%Y-%m-%dT%H:%M:%S')}.{value.microsecond // 1000:03d}Z"
        return value.strftime(DATE_FORMAT)
    raise TypeError(f"Expected datetime or str, got {type(value).__name__}")


def parse_date(value: Optional[Union[str, date]]) -> Optional[date]:
    """Parse a ``YYYY-MM-DD`` date-only string into a date.

    Args:
        value: A ``YYYY-MM-DD`` string, a date instance, or None.

    Returns:
        The date, or None if the input value is None or empty.

    Raises:
        TypeError: If value is a datetime, or not a string, date instance, or None.
        ValueError: If value is a string that is not a valid ``YYYY-MM-DD`` date.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        raise TypeError("Expected str or date, got datetime; use parse_datetime for instants")
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        match = _DATE_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError(f"Invalid date '{value}'; expected YYYY-MM-DD")
        return date(*(int(part) for part in match.groups()))
    raise TypeError(f"Expected str or date, got {type(value).__name__}")


def format_date(value: Optional[Union[date, str]]) -> Optional[str]:
    """Format a date into a ``YYYY-MM-DD`` wire string.

    Args:
        value: A date instance, a ``YYYY-MM-DD`` string (validated and returned unchanged), or None.

    Returns:
        The ``YYYY-MM-DD`` string, or None if the input value is None.

    Raises:
        TypeError: If value is a datetime, or not a date instance, string, or None.
        ValueError: If value is a string that is not a valid ``YYYY-MM-DD`` date.
    """
    if value is None:
        return None
    if isinstance(value, str):
        parse_date(value)
        return value
    if isinstance(value, datetime):
        raise TypeError("Expected date or str, got datetime; use format_datetime for instants")
    if isinstance(value, date):
        return f"{value.year:04d}-{value.month:02d}-{value.day:02d}"
    raise TypeError(f"Expected date or str, got {type(value).__name__}")


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
        value: An ISO-8601 instant string, a datetime instance, or None.

    Returns:
        UTC-aware datetime instance, or None if the input value is None or empty.
    """
    return parse_datetime(value)


__all__ = [
    "DATE_FORMAT",
    "format_date",
    "format_datetime",
    "from_wire_date",
    "parse_date",
    "parse_datetime",
    "to_wire_date",
]
