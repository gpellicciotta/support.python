# Wider instant parsing and date-only helpers in support_python.dates

## Technical Specifications
### Evidence
- `DATE_FORMAT` in `src/support_python/dates.py` is `%Y-%m-%dT%H:%M:%SZ`.
- `parse_datetime` calls `datetime.strptime(value, DATE_FORMAT)`, so fractions and offsets raise `ValueError`.
- `LogEntry.from_wire` in `src/support_python/models.py` parses timestamps through `parse_datetime`.
- todos.server stores and sends edit times with milliseconds, such as `2026-11-06T10:15:30.123Z`.
- `requires-python` is `>=3.9`; `datetime.fromisoformat` accepts a `Z` suffix only from Python 3.11.

### Required Behavior
- `parse_datetime` accepts `Z` instants with whole seconds or 1 to 6 fractional digits.
- `parse_datetime` accepts instants with a `+HH:MM` or `-HH:MM` offset, and returns them converted to UTC.
- Every parsed value is a UTC-aware `datetime`; `None`, empty strings, and `datetime` inputs behave as today.
- Malformed strings, date-only strings, and instants without a zone still raise `ValueError`.
- `format_datetime` keeps second precision by default, so existing output does not change.
- `format_datetime(value, millis=True)` emits exactly three fractional digits, such as `2026-11-06T10:15:30.123Z`.
- New `parse_date` turns `YYYY-MM-DD` into a `datetime.date`, and new `format_date` does the reverse.
- `parse_date` and `format_date` pass `None` through and raise `ValueError` on malformed input.
- The package root exports `parse_date` and `format_date`.

### Design Decisions
- **[Decided]** Keep `DATE_FORMAT` and the existing function signatures for backward compatibility.
- **[Decided]** Parse with a strict regular expression or explicit `strptime` patterns, not `fromisoformat`, to keep Python 3.9.

### Out of Scope
- Time zone conversion for display, and IANA time zone handling.
- Changing wire precision in `models.py` serializers.

### Tests
- Unit: `parse_datetime("2026-11-06T10:15:30.123Z")` returns 10:15:30.123000 UTC.
- Unit: `parse_datetime("2026-11-08T18:00:00+01:00")` returns 17:00:00 UTC.
- Unit: Six fractional digits parse, and seven or more raise `ValueError`.
- Unit: `"2026-11-06"`, `"2026-11-06T10:15:30"`, and `"not a date"` raise `ValueError` in `parse_datetime`.
- Unit: `format_datetime` output is unchanged by default, and `millis=True` yields three fractional digits.
- Unit: `parse_date("2026-11-04")` returns `date(2026, 11, 4)`, `format_date` round-trips it, and both pass `None` through.
- Integration: `LogEntry.from_wire` parses a log entry whose timestamp has milliseconds.

### Declared Files
- `src/support_python/dates.py`
- `src/support_python/__init__.py`
- `tests/test_dates.py`
- `docs/requirements.md`
- `docs/tutorials/rest-clients.md`
- `CHANGELOG.md`
