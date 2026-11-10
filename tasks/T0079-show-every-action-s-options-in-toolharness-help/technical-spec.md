### Declared Files
- src/support_python/cli.py
- tests/test_cli.py
- src/support_python/tools/processes.py
- docs/tutorials/cli-harness-and-logging.md
- CHANGELOG.md

### Tests
- Unit: A demo harness with a `--cwd PATH` action option shows it under that action in `help --verbose`.
- Unit: Per-action help prints `--cwd PATH` with a lowercase description.
- Integration: Run the installed `processes help --verbose` and confirm `--cwd`, `--format`, `--dry-run`, and `--force` appear under their actions.

Completion check: `.venv/Scripts/python -m pytest tests/test_cli.py tests/tools` plus the integration scenario above.
Size estimate: 5 files, 250 lines

### Notes
- `BackupHarness` in git-repository-backup overrides `format_help`; leave its hand-written help unchanged.
- Follow [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md).
