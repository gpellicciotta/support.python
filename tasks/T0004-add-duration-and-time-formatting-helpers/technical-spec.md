### Declared Files
- src/support_python/durations.py
- tests/test_durations.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 7 files, 400 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: format_duration: 59.04 -> '59.0s'; 125 -> '2m 05s'; 3725 -> '1h 02m 05s'; 90000 -> '1d 01h'; negative -> '0.0s'.
- Unit: format_short_duration: 45 -> '45s'; 119 -> '119s'; 120 -> '2m'; 41940 -> '11h 39m'; 108000 -> '1d 6h'.
- Unit: parse_duration_to_seconds accepts each supported unit, combined units, and default_unit; returns None for invalid or negative input.
- Unit: parse_iso8601 and parse_date_or_datetime return None for None or malformed text and handle date-only and timezone forms.
- Unit: format_epoch and format_past_epoch with a fixed now_ts give the documented 'YYYY-MM-DD HH:MM:SS (in ...)' and '(... ago)' strings.
- Integration: Round-trip across functions: parse a duration string, add it to a fixed epoch, and format it with format_epoch and format_past_epoch against an injected now_ts.

Completion check: python -m pytest tests/test_durations.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** New module durations.py, so the existing dates.py wire-date API stays untouched.
- **[Decided]** Name collisions with dates.py are resolved in favor of the existing function; document any skipped plan function.
