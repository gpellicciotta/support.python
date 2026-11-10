### Declared Files
- src/support_python/tools/processes.py
- tests/tools/test_processes.py
- src/support_python/processes.py
- docs/tools/processes.md
- CHANGELOG.md

### Tests
- Unit: `safe_kill` can report one result per PID, while its existing boolean callers keep working.
- Unit: `kill --dry-run --format json` reports `would-kill` and `would-skip-protected` outcomes and terminates nothing.
- Integration: Start a child Python process, run the installed `processes kill {{pid}} --format json`, and parse `stdout` as JSON.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_processes.py` plus the integration scenario above.
Size estimate: 5 files, 200 lines

### Notes
- Name JSON fields in lowercase kebab-case, consistent with the tool's existing JSON documents.
- Treat every field as a compatibility contract; T0081 later specifies the documents.
- Follow [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md).
