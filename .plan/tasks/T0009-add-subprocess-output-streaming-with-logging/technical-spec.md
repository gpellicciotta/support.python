### Declared Files
- src/support_python/devops.py (or a new streaming module)
- tests/test_streaming.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 7 files, 300 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: Lines from a child printing to stdout and stderr reach the logger in order with the origin tag; blank lines are skipped.
- Unit: The command line and PID are logged before output.
- Unit: The return value is the child's exit code; a missing executable returns the not-found code and logs an error.
- Unit: The per-line callback sees every raw line; callback exceptions do not kill the stream.
- Unit: KeyboardInterrupt during streaming terminates the child, then kills it after the 5 second wait, and re-raises (patched process).
- Integration: Run a real child Python process that prints 100 lines and exits 3, with a file-backed logger; assert the log file content and exit code 3.

Completion check: python -m pytest tests/test_streaming.py tests/test_devops.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Depends on T0005 for the unified logger.
- **[Decided]** The child is started with stdin set to DEVNULL, as in plan, so it cannot block on input.
- **[Decided]** run_step behavior must not change; existing devops tests stay green.
