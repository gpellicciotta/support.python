### Declared Files
- tests/conftest.py
- tests/test_conftest_guard.py
- AGENTS.md
- CHANGELOG.md

### Tests
- Unit: A test writing `Path.home() / 'leak.txt'` lands in the temporary home, never the real one.
- Unit: The guard reports a write into the repository's `.plan/` and fails the session.
- Integration: Run the full fast suite with the guard active and confirm it passes with no real-state writes.

Completion check: `.venv/Scripts/python -m pytest`, exiting 0 with the guard active.
Size estimate: 4 files, 150 lines

### Notes
- Snapshot only paths tests could plausibly touch, such as `~/.claude`, `~/.codex`, `~/.gemini`, and `.plan/`, to stay fast.
- Follow [testing-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/testing-guidelines.md).
