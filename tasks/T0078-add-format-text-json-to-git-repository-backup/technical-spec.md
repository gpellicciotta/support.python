### Declared Files
- src/support_python/tools/git_repository_backup.py
- tests/tools/test_git_repository_backup.py
- docs/tools/git-repository-backup.md
- CHANGELOG.md

### Tests
- Unit: `backup --format json` reports `updated`, `unchanged`, `skipped`, or `failed` per repository and layer.
- Unit: `restore --format json` reports the restored target, source, and checked-out branch.
- Integration: Back up and restore a temporary repository with the installed tool using `--format json`, parsing both documents.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_git_repository_backup.py` plus the integration scenario above.
Size estimate: 4 files, 200 lines

### Notes
- Name JSON fields in lowercase kebab-case, consistent with the tool's existing JSON documents.
- Treat every field as a compatibility contract; T0081 later specifies the documents.
- Follow [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md).
