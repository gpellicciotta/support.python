### Declared Files
- src/support_python/cli.py
- src/support_python/logging.py
- src/support_python/backup.py
- tests/test_cli.py
- tests/test_logging.py
- tests/test_backup_git_repos.py
- docs/index.md
- CHANGELOG.md

### Tests
- Unit: `test_cli.py` and `test_logging.py` cover every harness behavior from the diff list: help output, early-logger argument errors, exit codes, and lifecycle logging.
- Unit: `test_backup_git_repos.py` runs the existing backup, list, restore, and set-password cases against `support_python.backup`.
- Integration: `support-python backup list --config {{fixture-config}}` against a temporary repository tree exits 0 and lists the fixture repos.

Completion check: `python -m pytest tests -q && ruff check src tests`
