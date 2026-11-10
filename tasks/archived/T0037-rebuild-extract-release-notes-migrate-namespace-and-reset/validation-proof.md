## Walkthrough & Validation

### Key Changes
- The three scripts prepend `<script dir>/../src` when present, then import `support_python`.
- Each resolves its target with `get_repo_root(Path.cwd())`; outside a repository it exits 1.
- `extract-release-notes.py` skips repository resolution when an explicit changelog path is given.
- `support_python.git` gained `get_remote_url`, `parse_github_remote`, `get_github_repo`, and `get_default_branch`.
- `release.parse_github_repo` now delegates to `parse_github_remote`, so one regex remains.
- `migrate-namespace.py finish` uses `extract_release_notes`; the old regex returned empty notes for frozen layouts.
- `scripts/_repo_common.py` is deleted.

### Red Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_git.py tests/test_extract_release_notes.py tests/test_migrate_namespace.py -k "not rewrite and not reinit"`
Mutating tests were deselected because the old scripts would have targeted this worktree.

```text
ERROR tests/test_git.py - AttributeError: module 'support_python.git' has no attribute 'get_default_branch'
FAILED tests/test_extract_release_notes.py::TestExtractReleaseNotesScript::test_outside_repository_fails
FAILED tests/test_extract_release_notes.py::TestExtractReleaseNotesScript::test_reads_changelog_of_current_repository_from_subdirectory
FAILED tests/test_extract_release_notes.py::TestExtractReleaseNotesScript::test_this_repository_notes_from_subdirectory
FAILED tests/test_migrate_namespace.py::TestRepoScripts::test_build_runs_in_current_repository_root
FAILED tests/test_migrate_namespace.py::TestRepoScripts::test_reset_history_backup_inside_repo_is_refused
FAILED tests/test_migrate_namespace.py::TestRepoScripts::test_scripts_outside_repository_fail
6 failed, 6 passed, 3 deselected in 5.00s
```

### Full Suite (exit 0)
Command: `.venv/Scripts/python -m pytest -q`

```text
860 passed, 3 skipped, 81 subtests passed in 112.34s (0:01:52)
```

Command: `.venv/Scripts/ruff check . && .venv/Scripts/ruff format --check .` (exit 0)

```text
All checks passed!
134 files already formatted
```

### Integration (exit 0 each)
From a fresh temporary Git repository whose `CHANGELOG.md` has a `## v0.1.0 [2026-11-10]` section:

```text
$ python {{support-python}}/scripts/extract-release-notes.py 0.1.0
- Temporary repository notes.
exit=0
reset-history --help exit=0
migrate-namespace --help exit=0
1.3.5 exit=0
1.3.5 output identical to pre-change baseline
```

The baseline was captured with the old script before any change: `extract-release-notes.py 1.3.5 > old-1.3.5.txt`, compared by `cmp`.

### Markdown Lint
`lint-markdown check README.md CHANGELOG.md docs/devops.md` reports 10 issues, all on pre-existing lines.
None are in the new README section, the new CHANGELOG entries, or the edited `docs/devops.md` lines.
