## Walkthrough & Validation

### Key Changes
- Consolidated `ToolHarness` behavior in `src/support_python/cli.py` so bare invocations always print help, flag-prefixed arguments do not trigger `fallback_action`, `PROJECT_VERSION` is exported, and `support-python backup` dispatches to `support_python.backup.main`.
- Updated `format_log_message` in `src/support_python/logging.py` to preserve blank lines inside multi-line log messages.
- Copied `scripts/backup-git-repos.py` to `src/support_python/backup.py`, moved UTF-8 stream reconfiguration into `main()`, and fixed imports to use `support_python.cli` and `support_python.logging`.
- Updated `tests/test_cli.py`, `tests/test_logging.py`, and `tests/test_backup_git_repos.py` to test the merged harness behavior, `support_python.backup`, and the `support-python backup` CLI subcommand.
- Updated `CHANGELOG.md` (under `## v1.0.17-pre`) and `docs/index.md`.

### Red-Phase Test Failure Proof
Command: `python -m pytest tests/test_cli.py tests/test_logging.py -q`
Exit code: `1`
```text
[... 80 lines omitted ...]
=========================== short test summary info ===========================
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_bare_invocation_prints_help_and_fallback_action_dispatches_non_flags
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_support_python_backup_subcommand_dispatches
FAILED tests/test_logging.py::FormatLogMessageTests::test_multiline_message_preserves_blank_lines
3 failed, 41 passed in 3.67s
```

### Green-Phase Test Suite and Linter Verification
Command: `python -m pytest tests -q`
Exit code: `0`
```text
..................................................... [  9%]
........................................... [ 17%]
...................................................................... [ 30%]
.....................................................................s.. [ 43%]
........................................................................ [ 57%]
...................................s......s............................. [ 70%]
........................................................................ [ 83%]
........................................................................ [ 97%]
...............                                                          [100%]
538 passed, 3 skipped, 50 subtests passed in 150.40s (0:02:30)
```

Command: `ruff check src tests && ruff format --check src tests`
Exit code: `0`
```text
All checks passed!
58 files already formatted
```
