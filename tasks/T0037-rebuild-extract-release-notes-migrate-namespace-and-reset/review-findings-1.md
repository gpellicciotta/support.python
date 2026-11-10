---
task: T0037
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T02:46:26Z
reviewed_commit: "62e9332"
base_commit: "9a062b9"
branch: task/T0037-rebuild-extract-release-notes-migrate-namespace-and-reset
---
# Review Findings: Task T0037 (Round 1)

## Summary
Approved. The work meets the task goals.
- All three scripts import `support_python` from `<script dir>/../src` or an installed package.
- Each resolves its target with `get_repo_root(Path.cwd())` and exits 1 outside a repository.
- `scripts/_repo_common.py` is deleted, with no remaining references.
- `scripts/install-from-github-release.py` is untouched.
- New Git queries return `None` on failure, matching the module's convention.
- `release.parse_github_repo` now delegates to `parse_github_remote`, which removes a duplicate regex.

Independent verification on `62e9332`:
- `ruff check .` and `ruff format --check .` pass, with 134 files formatted.
- `python -m pytest -q`: 860 passed, 3 skipped, 81 subtests passed.
- A temporary repo, run from a subdirectory: `extract-release-notes.py 0.1.0` printed that repo's notes and exited 0.
- `reset-history.py --help` and `migrate-namespace.py --help` exited 0.
- `extract-release-notes.py 1.3.5` output is byte-identical to the `main` script's output (`cmp`).
- `lint-markdown` reports 10 issues, all on pre-existing lines.

## Defects
None blocking. Minor observations:
- `extract-release-notes.py` now exits 1 on an empty version section.
  The old script printed an empty line and exited 0, as verified against `main`.
  The library's `extract_release_notes` raises on empty notes.
  This is defensible for release notes, but neither the Execution Log nor CHANGELOG.md records it.
- Startup output changed slightly. `origin()` and `default_branch()` no longer echo their `$ git ...` commands.
  The typed prompt now reads "to continue" instead of "to proceed", because the spec requires `confirm_typed`.
- `next_major` now requires `MAJOR.MINOR.PATCH`. The old code only parsed the major component.
- `docs/devops.md` still lists `_tool_common.py` and `_harness.py` as shared helpers, but neither exists in `scripts/`.
  This stale text predates the task, but the edited line keeps it.

## Process Gaps
None blocking.
- The `migrate-namespace.py finish` release-notes fix has no test. The old regex returned empty notes for frozen layouts.
- Undeclared files (`__init__.py`, `release.py`, `README.md`, `docs/devops.md`) and the size overrun are logged in the Execution Log.

## Required Rework
None.
