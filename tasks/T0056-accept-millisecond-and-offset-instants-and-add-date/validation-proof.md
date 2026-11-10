## Walkthrough & Validation

### Red phase
`.venv/Scripts/python -m pytest -q tests/test_dates.py` and `tests/test_models.py`, before the implementation (exit 1):
```text
ImportError while importing test module 'C:\Dev-Projects\support.python\tests\test_dates.py'.
E   ImportError: cannot import name 'format_date' from 'support_python.dates' (C:\Dev-Projects\support.python\src\support_python\dates.py). Did you mean: 'format_table'?
FAILED tests/test_models.py::LogEntryTests::test_log_entry_from_wire_millisecond_timestamp
1 failed, 19 passed in 0.18s
```

### Green phase
`.venv/Scripts/python -m pytest -q tests/test_dates.py tests/test_models.py` (exit 0):
```text
42 passed, 18 subtests passed in 0.16s
```

`.venv/Scripts/python -m pytest -q` (exit 0):
```text
1091 passed, 3 skipped, 159 subtests passed in 118.89s (0:01:58)
```

`.venv/Scripts/ruff check src tests` (exit 0):
```text
All checks passed!
```

### Python 3.9 compatibility
`PYTHONPATH=src uv run --no-project --python 3.9 python -m unittest tests.test_dates tests.test_models` (exit 0):
```text
Ran 42 tests in 0.002s

OK
```

### Integration
`LogEntry.from_wire` with a millisecond timestamp, via `test_log_entry_from_wire_millisecond_timestamp`, plus a direct run:
```text
datetime.datetime(2026, 11, 6, 10, 15, 30, 123000, tzinfo=datetime.timezone.utc)
{'message': 'Edited', 'timestamp': '2026-11-06T10:15:30Z'}
```

### Review round 1 fixes
New offset-edge and out-of-range tests, before the `OverflowError` mapping (exit 1):
```text
E       OverflowError: date value out of range
SUBFAILED(value='0001-01-01T00:00:00+01:00') tests/test_dates.py::WiderInstantParsingTests::test_parse_datetime_offset_edges
SUBFAILED(value='9999-12-31T23:59:59-01:00') tests/test_dates.py::WiderInstantParsingTests::test_parse_datetime_offset_edges
```
After the fix, `.venv/Scripts/python -m pytest -q` (exit 0):
```text
1093 passed, 3 skipped, 162 subtests passed in 123.98s (0:02:03)
```
Python 3.9 rerun of `tests.test_dates tests.test_models`:
```text
Ran 44 tests in 0.002s

OK
```
