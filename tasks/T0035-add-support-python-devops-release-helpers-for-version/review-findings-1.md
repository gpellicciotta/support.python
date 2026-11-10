---
task: T0035
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T02:12:17Z
reviewed_commit: "f5a166c"
base_commit: "d041d23"
branch: task/T0035-add-support-python-devops-release-helpers-for-version
---
# Review Findings: Task T0035 (Round 1)

## Summary
Approved. `support_python.devops.release` implements every helper in the technical-spec API, stdlib-only.
All helpers are re-exported from `support_python.devops`.
Behavior matches the consolidated sources:
- `extract_release_notes` matches `scripts/extract-release-notes.py`, plus the spec's empty-section `ValueError`.
- Version-file patterns match `scripts/_repo_common.py`.
- `parse_github_repo` matches `scripts/install-from-github-release.py`.
- `freeze_changelog`, `open_dev_changelog`, and `next_dev_version` match the `template.python` devops helpers.
`next_dev_version` also gains the specified `part` argument.
Writes go through `atomic_write_text(..., newline="")`, which keeps line endings.
Scripts are untouched, as the goals require.

Independent verification in the worktree:
- `.venv/Scripts/python -m pytest -q`: 813 passed, 3 skipped, 81 subtests passed.
- `ruff check .`: all checks passed; `ruff format --check .`: 134 files already formatted.
- `plan validate T0035`: passed; the TF018 error from the log is resolved.
- `RepositoryIntegrationTests` covers both spec integration checks: version equals CHANGELOG top version, and 1.3.5 notes equal script output.
- Manual edge checks: `open_dev_changelog` on a separator at EOF and `freeze_changelog` on a heading with trailing spaces behave sensibly.
- New README lines stay within 132 characters.

The tests cover every unit case listed under `### Tests`, including CRLF preservation for all three version files and the CHANGELOG helpers.

## Defects
None.

Non-blocking observations:
- `VERSION_FILES` order is `pyproject.toml`, `gradle.properties`, `package.json`, per the spec.
  `scripts/_repo_common.py` checks `gradle.properties` first.
  T0037 should know about this difference when it rebuilds the scripts.
- `open_dev_changelog` also matches a `---` on line 1, while the template helper required `\n---\n`.
  This matters only if a CHANGELOG starts with front matter, which the convention does not use.

## Process Gaps
- `tests/test_devops.py` changed but is not under `### Declared Files`.
  The change was required, since that test pins `devops.__all__`, and the Execution Log records it. Not blocking.

## Required Rework
None.
