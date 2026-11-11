### Declared Files
- src/support_python/cli.py
- tests/test_cli.py
- docs/tutorials/cli-harness-and-logging.md
- CHANGELOG.md

### Tests
- Unit: `ToolHarness("demo", "Demo.", version="3.0.0rc0").format_version()` starts with `demo v3.0.0-pre`.
- Unit: versions such as `3.0.0rc1`, `3.0.0`, and `3.0.0-pre` pass through unchanged.
- Integration: a `run_cli` capture of `demo --version` for a harness built with an `rc0` version prints the `-pre` form.

Completion check: `python -m pytest tests/test_cli.py` passes.

Size estimate: 4 files, 40 lines
