"""Duration and timestamp parsing and formatting utilities.

Provides human-readable duration formatting, compound duration parsing,
flexible ISO-8601 and date/datetime parsing, and relative epoch formatting.
Does not define ``format_datetime`` so :func:`support_python.dates.format_datetime`
remains the sole wire-datetime formatter in the package.
"""

from __future__ import annotations

from datetime import datetime
import re
import time


def parse_iso8601(text: str | None) -> float | None:
    """Parse an ISO 8601 timestamp string into a POSIX epoch timestamp.

    Handles trailing ``'Z'`` as a UTC timezone indicator.

    Args:
        text: An ISO 8601 formatted timestamp string, or None.

    Returns:
        The POSIX timestamp in seconds as a float, or None if input is empty or invalid.
    """
    if not text:
        return None
    s = text.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s).timestamp()
    except ValueError:
        return None


def parse_date_or_datetime(text: str | None) -> datetime | None:
    """Parse a date or timestamp string into a naive datetime object.

    Supports ``'YYYY-MM-DD'``, ``'YYYY-MM-DD HH:MM:SS'``, ``'YYYY-MM-DDTHH:MM:SS'``,
    ``'YYYY-MM-DD HH:MM'``, ``'YYYY-MM-DDTHH:MM'``, and ``YYYY-MM-DD`` date prefixes.

    Args:
        text: Date or timestamp string, or None.

    Returns:
        Parsed naive datetime object, or None if input is empty or invalid.
    """
    if not text:
        return None
    s = text.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", s)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return None


def parse_duration_to_seconds(
    dur_str: str | None,
    default_unit: str = "s",
) -> float | None:
    """Parse duration strings into total seconds.

    Supports compound and single units such as ``'30s'``, ``'15m'``, ``'2h'``,
    ``'1h30m'``, ``'1d'``, ``'500ms'``, or bare numbers (interpreted using
    ``default_unit``, where ``'ms'`` converts to seconds).

    Args:
        dur_str: Duration string representation, or None.
        default_unit: Fallback unit for bare numbers (``'s'`` for seconds, ``'ms'`` for milliseconds).

    Returns:
        Duration in seconds as a float, or None if invalid or negative.
    """
    if not dur_str:
        return None
    s = dur_str.strip().lower()
    if not s:
        return None

    try:
        val = float(s)
        if val < 0:
            return None
        return val / 1000.0 if default_unit == "ms" else val
    except ValueError:
        pass

    if "-" in s:
        return None

    total = 0.0
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*(ms|[dhms])", s)
    if not matches:
        return None

    unit_multipliers = {
        "d": 86400.0,
        "h": 3600.0,
        "m": 60.0,
        "s": 1.0,
        "ms": 0.001,
    }
    for val_str, unit in matches:
        total += float(val_str) * unit_multipliers[unit]

    return total if total >= 0 else None


def format_duration(seconds: float | int) -> str:
    """Format a duration in seconds to a concise human-readable string.

    Examples: ``'1h 02m 05s'``, ``'1d 01h'``, or ``'59.0s'``. Durations of 24 hours
    or more drop to day/hour granularity. Negative values clamp to ``'0.0s'``.

    Args:
        seconds: Duration in seconds.

    Returns:
        Concise formatted duration string.
    """
    sec_float = float(seconds)
    if sec_float < 0:
        return "0.0s"
    if sec_float < 60:
        return f"{sec_float:.1f}s"
    mins, secs = divmod(int(sec_float), 60)
    hours, mins = divmod(mins, 60)
    days, hours = divmod(hours, 24)
    if days > 0:
        return f"{days}d {hours:02d}h"
    if hours > 0:
        return f"{hours}h {mins:02d}m {secs:02d}s"
    return f"{mins}m {secs:02d}s"


def format_short_duration(seconds: float | int) -> str:
    """Format a duration in seconds without seconds above 2 minutes.

    - Under 120 seconds: ``'<secs>s'`` (e.g. ``'45s'``, ``'119s'``)
    - 120 seconds to under 1 hour: ``'<minutes>m'`` (e.g. ``'2m'``, ``'21m'``)
    - 1 hour to under 1 day: ``'<hours>h <minutes>m'`` (e.g. ``'11h 39m'``)
    - 1 day or more: ``'<days>d <hours>h'`` (e.g. ``'1d 6h'``)

    Args:
        seconds: Duration in seconds.

    Returns:
        Short formatted duration string.
    """
    secs = max(0, int(float(seconds)))
    if secs < 120:
        return f"{secs}s"
    total_mins = secs // 60
    if total_mins < 60:
        return f"{total_mins}m"
    total_hours, rem_mins = divmod(total_mins, 60)
    if total_hours < 24:
        return f"{total_hours}h {rem_mins}m"
    days, rem_hours = divmod(total_hours, 24)
    return f"{days}d {rem_hours}h"


def format_epoch(ts: float, now_ts: float | None = None) -> str:
    """Format an epoch timestamp to local datetime with relative remaining duration.

    Example: ``'2026-09-11 12:00:00 (in 2h 15m 30s)'``.

    Args:
        ts: Target epoch timestamp in seconds.
        now_ts: Current epoch timestamp, or None to use ``time.time()``.

    Returns:
        Formatted local datetime and remaining wait string.
    """
    dt = datetime.fromtimestamp(ts)
    curr = now_ts if now_ts is not None else time.time()
    wait_s = max(0, int(ts - curr))
    return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} (in {format_duration(wait_s)})"


def format_past_epoch(ts: float, now_ts: float | None = None) -> str:
    """Format a past epoch timestamp as ``'YYYY-MM-DD HH:MM (<duration> ago)'``.

    Args:
        ts: Past epoch timestamp in seconds.
        now_ts: Current epoch timestamp, or None to use ``time.time()``.

    Returns:
        Formatted local datetime and elapsed duration string.
    """
    dt = datetime.fromtimestamp(ts)
    curr = now_ts if now_ts is not None else time.time()
    elapsed_s = max(0.0, curr - ts)
    return f"{dt.strftime('%Y-%m-%d %H:%M')} ({format_short_duration(elapsed_s)} ago)"


__all__ = [
    "format_duration",
    "format_epoch",
    "format_past_epoch",
    "format_short_duration",
    "parse_date_or_datetime",
    "parse_duration_to_seconds",
    "parse_iso8601",
]
