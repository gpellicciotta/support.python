### Declared Files
- src/support_python/tools/git_repository_backup.py
- tests/tools/test_git_repository_backup.py
- docs/tools/git-repository-backup.md
- CHANGELOG.md

### Tests
- Unit: `GIT_REPOSITORY_BACKUP_DEPTH=3` beats the user file and loses to `--depth 1`; an empty variable counts as unset.
- Unit: A system file supplies `mirror-dir` when no higher source does; unknown keys appear in debug output only.
- Unit: Malformed user JSON warns once naming the file and falls through to defaults instead of exiting 2.
- Integration: Run the installed `git-repository-backup config list --format json`, `config set depth 4 --user`, and `config get depth --source` against a temporary `XDG_CONFIG_HOME`.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_git_repository_backup.py` plus the integration scenario above.
Size estimate: 4 files, 380 lines

### Notes
- Settings: `roots` (list), `mirror-dir`, `archive-dir`, `depth` (integer), `seven-zip`, `password-env`, `password-keyring`.
- Keep `--no-mirror`, `--no-archive`, `--dry-run`, and the restore options command-line only.
- `BackupHarness` keeps its hand-written help; add the `config` actions to it and to that help text.
- Follow [configuration-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md).
