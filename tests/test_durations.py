"""Unit and integration tests for support_python.durations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import support_python
from support_python import (
    format_datetime,
    format_duration,
    format_epoch,
    format_past_epoch,
    format_short_duration,
    parse_date_or_datetime,
    parse_duration_to_seconds,
    parse_iso8601,
)
import support_python.dates as dates
import support_python.durations as durations


def test_format_duration() -> None:
    assert format_duration(0) == "0.0s"
    assert format_duration(-1) == "0.0s"
    assert format_duration(-0.1) == "0.0s"
    assert format_duration(12.3) == "12.3s"
    assert format_duration(59.04) == "59.0s"
    assert format_duration(60) == "1m 00s"
    assert format_duration(125) == "2m 05s"
    assert format_duration(3600) == "1h 00m 00s"
    assert format_duration(3725) == "1h 02m 05s"
    assert format_duration(86400) == "1d 00h"
    assert format_duration(90000) == "1d 01h"
    assert format_duration(190800) == "2d 05h"


def test_format_short_duration() -> None:
    assert format_short_duration(-10) == "0s"
    assert format_short_duration(0) == "0s"
    assert format_short_duration(45) == "45s"
    assert format_short_duration(119) == "119s"
    assert format_short_duration(119.9) == "119s"
    assert format_short_duration(120) == "2m"
    assert format_short_duration(1260) == "21m"
    assert format_short_duration(3599) == "59m"
    assert format_short_duration(3600) == "1h 0m"
    assert format_short_duration(41940) == "11h 39m"
    assert format_short_duration(86400) == "1d 0h"
    assert format_short_duration(108000) == "1d 6h"


def test_parse_duration_to_seconds() -> None:
    assert parse_duration_to_seconds(None) is None
    assert parse_duration_to_seconds("") is None
    assert parse_duration_to_seconds("   ") is None
    assert parse_duration_to_seconds("invalid") is None
    assert parse_duration_to_seconds("-5") is None
    assert parse_duration_to_seconds("-10", default_unit="ms") is None

    # Bare numbers and default_unit
    assert parse_duration_to_seconds("30") == pytest.approx(30.0)
    assert parse_duration_to_seconds("0") == pytest.approx(0.0)
    assert parse_duration_to_seconds("500", default_unit="ms") == pytest.approx(0.5)

    # Single units
    assert parse_duration_to_seconds("500ms") == pytest.approx(0.5)
    assert parse_duration_to_seconds("30s") == pytest.approx(30.0)
    assert parse_duration_to_seconds("15m") == pytest.approx(900.0)
    assert parse_duration_to_seconds("2h") == pytest.approx(7200.0)
    assert parse_duration_to_seconds("1d") == pytest.approx(86400.0)
    assert parse_duration_to_seconds("1.5h") == pytest.approx(5400.0)

    # Combined units and whitespace/casing
    assert parse_duration_to_seconds("1h30m") == pytest.approx(5400.0)
    assert parse_duration_to_seconds("1d 2h 3m 4s 500ms") == pytest.approx(86400.0 + 7200.0 + 180.0 + 4.5)
    assert parse_duration_to_seconds("  2H 15M ") == pytest.approx(8100.0)


def test_parse_iso8601_and_parse_date_or_datetime() -> None:
    assert parse_iso8601(None) is None
    assert parse_iso8601("") is None
    assert parse_iso8601("   ") is None
    assert parse_iso8601("not-a-timestamp") is None

    expected_utc = datetime(2026, 9, 11, 12, 0, 0, tzinfo=timezone.utc).timestamp()
    assert parse_iso8601("2026-09-11T12:00:00Z") == pytest.approx(expected_utc)
    assert parse_iso8601("  2026-09-11T12:00:00+00:00  ") == pytest.approx(expected_utc)
    assert parse_iso8601("2026-09-11T14:00:00+02:00") == pytest.approx(expected_utc)

    date_only_ts = parse_iso8601("2026-09-11")
    assert date_only_ts == pytest.approx(datetime(2026, 9, 11, 0, 0, 0).timestamp())

    assert parse_date_or_datetime(None) is None
    assert parse_date_or_datetime("") is None
    assert parse_date_or_datetime("   ") is None
    assert parse_date_or_datetime("not-a-date") is None
    assert parse_date_or_datetime("2026-13-40") is None
    assert parse_date_or_datetime("2026-13-40 extra") is None

    assert parse_date_or_datetime("2026-09-11") == datetime(2026, 9, 11, 0, 0, 0)
    assert parse_date_or_datetime("2026-09-11 12:30") == datetime(2026, 9, 11, 12, 30, 0)
    assert parse_date_or_datetime("2026-09-11T12:30") == datetime(2026, 9, 11, 12, 30, 0)
    assert parse_date_or_datetime("2026-09-11 12:30:45") == datetime(2026, 9, 11, 12, 30, 45)
    assert parse_date_or_datetime("2026-09-11T12:30:45") == datetime(2026, 9, 11, 12, 30, 45)
    # Date prefix with trailing timezone or text falls back to date prefix
    assert parse_date_or_datetime("2026-09-11T12:30:45Z") == datetime(2026, 9, 11, 0, 0, 0)
    assert parse_date_or_datetime("2026-09-11T12:30:45+02:00") == datetime(2026, 9, 11, 0, 0, 0)


def test_format_epoch_and_format_past_epoch() -> None:
    target_dt = datetime(2026, 9, 11, 12, 0, 0)
    target_ts = target_dt.timestamp()
    now_ts = (target_dt - timedelta(hours=2, minutes=15, seconds=30)).timestamp()

    assert format_epoch(target_ts, now_ts=now_ts) == "2026-09-11 12:00:00 (in 2h 15m 30s)"
    # When target is in the past relative to now_ts, wait clamps to 0 -> '0.0s'
    assert format_epoch(now_ts, now_ts=target_ts) == "2026-09-11 09:44:30 (in 0.0s)"

    past_dt = datetime(2026, 9, 11, 9, 44, 0)
    past_ts = past_dt.timestamp()
    later_ts = (past_dt + timedelta(hours=2, minutes=16)).timestamp()
    assert format_past_epoch(past_ts, now_ts=later_ts) == "2026-09-11 09:44 (2h 16m ago)"
    # When ts is in the future relative to now_ts, elapsed clamps to 0 -> '0s'
    assert format_past_epoch(later_ts, now_ts=past_ts) == "2026-09-11 12:00 (0s ago)"


def test_integration_round_trip_and_export_surface() -> None:
    base_iso = "2026-09-11T10:00:00Z"
    base_ts = parse_iso8601(base_iso)
    assert base_ts is not None

    delta_s = parse_duration_to_seconds("1h 02m 05s")
    assert delta_s == pytest.approx(3725.0)

    future_ts = base_ts + delta_s
    future_local_str = datetime.fromtimestamp(future_ts).strftime("%Y-%m-%d %H:%M:%S")
    base_local_hm = datetime.fromtimestamp(base_ts).strftime("%Y-%m-%d %H:%M")

    formatted_future = format_epoch(future_ts, now_ts=base_ts)
    assert formatted_future == f"{future_local_str} (in 1h 02m 05s)"

    formatted_past = format_past_epoch(base_ts, now_ts=future_ts)
    assert formatted_past == f"{base_local_hm} (1h 2m ago)"

    parsed_back = parse_date_or_datetime(future_local_str)
    assert parsed_back == datetime.fromtimestamp(future_ts).replace(microsecond=0)

    # Ensure dates.format_datetime is preserved and not shadowed by durations
    assert format_datetime is dates.format_datetime
    assert not hasattr(durations, "format_datetime")
    assert not hasattr(durations, "extract_reset_time_from_text")
    assert not hasattr(durations, "extract_rate_limit_reset")
    assert support_python.format_duration is durations.format_duration
    assert support_python.format_short_duration is durations.format_short_duration
    assert support_python.parse_duration_to_seconds is durations.parse_duration_to_seconds
    assert support_python.parse_iso8601 is durations.parse_iso8601
    assert support_python.parse_date_or_datetime is durations.parse_date_or_datetime
    assert support_python.format_epoch is durations.format_epoch
    assert support_python.format_past_epoch is durations.format_past_epoch
