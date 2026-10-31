"""Tests for support_python.dates module."""

from datetime import datetime, timedelta, timezone
import unittest

from support_python.dates import (
    DATE_FORMAT,
    format_datetime,
    from_wire_date,
    parse_datetime,
    to_wire_date,
)


class DateTimeHelpersTests(unittest.TestCase):
    def test_date_format_constant(self) -> None:
        self.assertEqual(DATE_FORMAT, "%Y-%m-%dT%H:%M:%SZ")

    def test_parse_datetime_valid_utc_string(self) -> None:
        dt = parse_datetime("2026-08-21T12:00:00Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt, datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc))

    def test_parse_datetime_none_or_empty(self) -> None:
        self.assertIsNone(parse_datetime(None))
        self.assertIsNone(parse_datetime(""))

    def test_parse_datetime_datetime_input(self) -> None:
        naive = datetime(2026, 8, 21, 12, 0, 0)
        parsed = parse_datetime(naive)
        self.assertEqual(parsed, datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc))

        tz_offset = timezone(timedelta(hours=2))
        aware = datetime(2026, 8, 21, 14, 0, 0, tzinfo=tz_offset)
        parsed_aware = parse_datetime(aware)
        self.assertEqual(parsed_aware, datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc))

    def test_parse_datetime_invalid_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_datetime("invalid-date")

    def test_parse_datetime_invalid_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            parse_datetime(12345)  # type: ignore

    def test_format_datetime_utc_datetime(self) -> None:
        dt = datetime(2026, 8, 21, 12, 30, 45, tzinfo=timezone.utc)
        self.assertEqual(format_datetime(dt), "2026-08-21T12:30:45Z")

    def test_format_datetime_naive_assumes_utc(self) -> None:
        dt = datetime(2026, 8, 21, 12, 30, 45)
        self.assertEqual(format_datetime(dt), "2026-08-21T12:30:45Z")

    def test_format_datetime_non_utc_converts(self) -> None:
        tz_offset = timezone(timedelta(hours=2))
        dt = datetime(2026, 8, 21, 14, 30, 45, tzinfo=tz_offset)
        self.assertEqual(format_datetime(dt), "2026-08-21T12:30:45Z")

    def test_format_datetime_none_and_string(self) -> None:
        self.assertIsNone(format_datetime(None))
        self.assertEqual(format_datetime("2026-08-21T12:00:00Z"), "2026-08-21T12:00:00Z")

    def test_format_datetime_invalid_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            format_datetime(12345)  # type: ignore

    def test_datetime_round_trip(self) -> None:
        original = datetime(2026, 9, 18, 14, 0, 0, tzinfo=timezone.utc)
        formatted = format_datetime(original)
        self.assertEqual(formatted, "2026-09-18T14:00:00Z")
        self.assertEqual(parse_datetime(formatted), original)

    def test_wire_date_aliases(self) -> None:
        dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        wire_str = "2026-01-01T00:00:00Z"
        self.assertEqual(to_wire_date(dt), wire_str)
        self.assertEqual(from_wire_date(wire_str), dt)


if __name__ == "__main__":
    unittest.main()
