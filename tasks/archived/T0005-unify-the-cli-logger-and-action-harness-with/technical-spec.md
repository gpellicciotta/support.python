### Declared Files
- src/support_python/cli.py (harness) and src/support_python/logging.py
- tests/test_cli.py and tests/test_logging.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 8 files, 600 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: Registering actions yields the standard '{name} v{version} - {copyright}' banner, help, and version output.
- Unit: A bare invocation prints help; a configured fallback action runs instead when set.
- Unit: Handlers return exit codes that main propagates; the exit-code table appears in verbose help.
- Unit: resolve_log_level honors explicit level, debug flag, and default; padding stays at 11 characters.
- Unit: Build metadata appends '+<hash>' when available and is omitted when git is missing.
- Unit: The logger tees to a log file and the console with matching content; existing CliLogger and build_action_parser tests still pass.
- Integration: Run a demo CLI built on the harness through subprocess: help, version, an action, a failing action, and an invalid argument, asserting output headers, log file content, and exit codes 0, 1, 2.

Completion check: python -m pytest tests/test_cli.py tests/test_logging.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Existing public API (CliLogger, LogLevel, build_action_parser, print_version, print_help) stays source-compatible; additions only.
- **[Decided]** Size note: the source harness alone is about 480 lines, so this task likely exceeds the typical line. It stays one task because it is one subsystem (CLI) and a split would leave an unmergeable half.
- **[Decided]** Local copies in this repo's scripts/ (_harness.py, _tool_common.py) are follow-up migration targets, not part of this task.
