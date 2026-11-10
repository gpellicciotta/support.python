## Walkthrough & Validation

### Summary of Changes
- Added `support_python.devops.release` with `VersionFile`, `VERSION_FILES`, and the version, CHANGELOG, notes, and GitHub helpers.
- Version files are read and written byte-faithfully and atomically through `atomic_write_text(..., newline="")`.
- CHANGELOG helpers keep the newline style they find, including CRLF.
- Re-exported every helper from `support_python.devops` and added the names to `tests/test_devops.py`.
- Documented the helpers in README.md and added a v2.0.19-pre CHANGELOG.md entry.

### Red Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_release.py` (before implementation), exit code 2.
```text
tests\test_devops_release.py:10: in <module>
    from support_python.devops import (
E   ImportError: cannot import name 'VERSION_FILES' from 'support_python.devops' (C:\Dev-Projects\support.python\.plan\work\T0035-add-support-python-devops-release-helpers-for-version\src\support_python\devops\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_devops_release.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.35s
```

### Green Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_release.py`, exit code 0.
```text
.....................................                                    [100%]
37 passed in 0.21s
```

Command: `.venv/Scripts/python -m pytest -q`, run from the worktree, exit code 0.
```text
813 passed, 3 skipped, 81 subtests passed in 84.40s (0:01:24)
```

Commands: `.venv/Scripts/ruff check .` and `.venv/Scripts/ruff format --check .`, exit code 0.
```text
All checks passed!
134 files already formatted
```

### Repository Integration Scenario
The shared venv's editable install targets the main checkout, so manual checks set `PYTHONPATH=src`.
pytest uses the worktree `src` through `pythonpath = ["src"]` and runs both checks in `RepositoryIntegrationTests`.

Check 1: `read_version(Path("."))` and `changelog_top_version` of CHANGELOG.md, printed side by side.
```text
2.0.19-pre 2.0.19-pre
```

Check 2: library `extract_release_notes(text, "1.3.5")` written to a file, compared by `cmp` with the script output.
Script command: `PYTHONUTF8=1 .venv/Scripts/python scripts/extract-release-notes.py 1.3.5 > script-notes.txt`.
```text
IDENTICAL
```

### Markdown Lint
`lint-markdown check README.md CHANGELOG.md` reports 10 issues, none on lines this task added.
