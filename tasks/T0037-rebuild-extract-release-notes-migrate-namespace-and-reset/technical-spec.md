### Changes
- Each script prepends `<script dir>/../src` to `sys.path` when that directory exists, then imports `support_python`,
  so it works from a checkout and with an installed package.
- Resolve the target repository with `git rev-parse --show-toplevel` from the current directory; outside a repository,
  print an error and exit 1.
- Replace `_repo_common` helpers:
  - version and CHANGELOG helpers come from `support_python.devops.release`;
  - typed confirmations use `confirm_typed` from T0036;
  - add `default_branch` and origin owner/name queries to `support_python.git` when no equivalent exists;
  - keep `die`-style error exits inline.
- The default build command in `migrate-namespace.py` stays `python scripts/devops.py check`, relative to the target repository.

### Declared Files
- scripts/extract-release-notes.py
- scripts/migrate-namespace.py
- scripts/reset-history.py
- src/support_python/git.py
- tests/test_git.py
- tests/test_extract_release_notes.py
- tests/test_migrate_namespace.py
- CHANGELOG.md

### Tests
- Unit: `extract-release-notes.py 1.3.5` output for this repository is unchanged.
- Unit: the existing migrate-namespace tests pass, and each script run from a temporary repository acts on that repository.
- Unit: new `support_python.git` queries return the default branch and origin owner/name, or `None` on failure.
- Integration: from a temporary Git repository with its own `CHANGELOG.md`,
  `python {{support-python}}/scripts/extract-release-notes.py 0.1.0` prints that repository's notes.
- Integration: `reset-history.py --help` and `migrate-namespace.py --help` exit 0.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration commands above.
Size estimate: 8 files, 400 lines.
