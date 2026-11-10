"""Tests for support_python.dates module."""

from datetime import date, datetime, timedelta, timezone
import unittest

from support_python.dates import (
    DATE_FORMAT,
    format_date,
    format_datetime,
    from_wire_date,
    parse_date,
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


class WiderInstantParsingTests(unittest.TestCase):
    def test_parse_datetime_milliseconds(self) -> None:
        self.assertEqual(parse_datetime("2026-11-06T10:15:30.123Z"), datetime(2026, 11, 6, 10, 15, 30, 123000, tzinfo=timezone.utc))

    def test_parse_datetime_fraction_lengths(self) -> None:
        self.assertEqual(parse_datetime("2026-11-06T10:15:30.5Z").microsecond, 500000)
        self.assertEqual(parse_datetime("2026-11-06T10:15:30.123456Z").microsecond, 123456)
        with self.assertRaises(ValueError):
            parse_datetime("2026-11-06T10:15:30.1234567Z")
        with self.assertRaises(ValueError):
            parse_datetime("2026-11-06T10:15:30.Z")

    def test_parse_datetime_offsets_convert_to_utc(self) -> None:
        self.assertEqual(parse_datetime("2026-11-08T18:00:00+01:00"), datetime(2026, 11, 8, 17, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(
            parse_datetime("2026-11-08T18:00:00.250-05:30"), datetime(2026, 11, 8, 23, 30, 0, 250000, tzinfo=timezone.utc)
        )
        self.assertEqual(parse_datetime("2026-11-08T18:00:00+00:00").tzinfo, timezone.utc)

    def test_parse_datetime_offset_edges(self) -> None:
        self.assertEqual(parse_datetime("2026-01-01T00:30:00+01:00"), datetime(2025, 12, 31, 23, 30, tzinfo=timezone.utc))
        self.assertEqual(parse_datetime("2026-12-31T23:30:00-01:00"), datetime(2027, 1, 1, 0, 30, tzinfo=timezone.utc))
        self.assertEqual(parse_datetime("2026-11-08T18:00:00-00:00"), datetime(2026, 11, 8, 18, 0, tzinfo=timezone.utc))
        self.assertEqual(parse_datetime("2024-02-29T12:00:00Z"), datetime(2024, 2, 29, 12, 0, tzinfo=timezone.utc))
        for value in ("2026-11-06T10:15:30+01:60", "0001-01-01T00:00:00+01:00", "9999-12-31T23:59:59-01:00"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_datetime(value)

    def test_parse_datetime_rejects_dates_naive_and_malformed(self) -> None:
        for value in (
            "2026-11-06",
            "2026-11-06T10:15:30",
            "not a date",
            "2026-11-06 10:15:30Z",
            "2026-11-06T10:15:30+0100",
            "2026-11-06T10:15:30+24:00",
            "2026-02-30T10:15:30Z",
            "2026-11-06T10:15:30Z ",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_datetime(value)

    def test_format_datetime_default_is_unchanged_and_millis_option(self) -> None:
        value = datetime(2026, 11, 6, 10, 15, 30, 123987, tzinfo=timezone.utc)
        self.assertEqual(format_datetime(value), "2026-11-06T10:15:30Z")
        self.assertEqual(format_datetime(value, millis=True), "2026-11-06T10:15:30.123Z")
        self.assertEqual(format_datetime(datetime(2026, 11, 6, 10, 15, 30), millis=True), "2026-11-06T10:15:30.000Z")
        offset = datetime(2026, 11, 8, 18, 0, 0, 5000, tzinfo=timezone(timedelta(hours=1)))
        self.assertEqual(format_datetime(offset, millis=True), "2026-11-08T17:00:00.005Z")
        self.assertEqual(parse_datetime(format_datetime(value, millis=True)), value.replace(microsecond=123000))


class DateOnlyHelpersTests(unittest.TestCase):
    def test_parse_date(self) -> None:
        self.assertEqual(parse_date("2026-11-04"), date(2026, 11, 4))
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date(""))
        self.assertEqual(parse_date(date(2026, 11, 4)), date(2026, 11, 4))

    def test_parse_date_rejects_malformed(self) -> None:
        for value in ("2026-11-4", "20261104", "2026-11-04T00:00:00Z", "2026-13-01", "2026-02-30", "not a date"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_date(value)
        for value in (datetime(2026, 11, 4), 20261104):
            with self.subTest(value=value), self.assertRaises(TypeError):
                parse_date(value)  # type: ignore[arg-type]

    def test_format_date(self) -> None:
        self.assertEqual(format_date(date(2026, 11, 4)), "2026-11-04")
        self.assertIsNone(format_date(None))
        self.assertEqual(format_date("2026-11-04"), "2026-11-04")
        self.assertEqual(parse_date(format_date(date(2026, 1, 9))), date(2026, 1, 9))
        with self.assertRaises(ValueError):
            format_date("2026-11-4")
        with self.assertRaises(TypeError):
            format_date(datetime(2026, 11, 4))  # type: ignore[arg-type]

    def test_package_root_exports_date_helpers(self) -> None:
        import support_python

        for name in ("parse_date", "format_date"):
            with self.subTest(name=name):
                self.assertIn(name, support_python.__all__)
                self.assertIs(getattr(support_python, name), getattr(support_python.dates, name))


if __name__ == "__main__":
    unittest.main()
