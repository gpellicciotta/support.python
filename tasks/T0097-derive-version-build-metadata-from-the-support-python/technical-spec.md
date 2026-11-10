### Declared Files
- src/support_python/cli.py
- tests/test_cli.py
- docs/tutorials/cli-harness-and-logging.md
- CHANGELOG.md

### Tests
- Unit: `resolve_build_metadata` extracts short commit hash from distribution install metadata (`direct_url.json`).
- Unit: `resolve_build_metadata` returns `unknown` when `support_python` is located inside an enclosing foreign Git repository.
- Integration: a test installing into a venv inside a foreign Git repository shows no foreign hash for `agent-files version` and `--version`.

Completion check: `python -m pytest tests/test_cli.py` passes.

Size estimate: 4 files, 80 lines
