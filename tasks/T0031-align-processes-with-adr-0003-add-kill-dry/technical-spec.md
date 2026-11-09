### Command-Line Interface
```text
processes kill PID... [--force] [--dry-run]
processes list [filters] [--format text|json]
```
- `kill --dry-run` prints, per PID, whether it would be terminated or skipped as protected, and exits 0.
- `--format text` produces today's table output; `--format table` exits 2.

### Declared Files
- src/support_python/tools/processes.py
- tests/tools/test_processes.py
- docs/tools/processes.md
- docs/index.md
- README.md
- CHANGELOG.md

### Tests
- Unit: `kill --dry-run` calls no termination function (mocked) and reports would-kill or protected per PID.
- Unit: default `list` output matches the former table output; `--format table` exits 2.
- Integration: the test starts a child `python -c "import time; time.sleep(60)"`, runs installed `processes kill <pid> --dry-run`,
  asserts the child is alive, then runs `processes kill <pid>` and asserts it exited.
  Clean up only through the tool under test, never with raw OS kill calls.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration scenario above.
Size estimate: 6 files, 250 lines.
