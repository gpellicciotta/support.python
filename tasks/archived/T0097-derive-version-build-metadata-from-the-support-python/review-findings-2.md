---
task: T0097
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-10T21:24:47Z
reviewed_commit: "a504d0e"
base_commit: "4b44ff9"
branch: task/T0097-derive-version-build-metadata-from-the-support-python
---
# Review Findings: Task T0097 (Round 2)

## Summary
Round 1 rework is resolved. The goal is met, and the round 1 regression is fixed.
- `_is_support_python_target` now matches only when `work_dir` is the package dir, inside it, or inside the support-python checkout root. An ancestor of the package no longer matches, and no directory-name heuristics remain.
- A consumer repo with its own `.venv` keeps its own hash. A wheel in a foreign venv shows no foreign hash. Install-time `direct_url.json` commits are read. Source and editable checkouts report their own hash.

Evidence:
- `pytest tests/test_cli.py` passed: 36 passed, 25 subtests passed. This includes `test_foreign_repo_with_venv_keeps_own_hash`, `test_source_or_editable_checkout_returns_checkout_hash`, and the foreign-venv wheel integration test.
- `pytest tests` had 1228 passed, 3 skipped, and 1 error. The error is the conftest user-state guard on `~/.claude/skills/synced`, which this change does not touch. It is the same error as round 1.
- `ruff check` and `ruff format --check` were clean.
- CHANGELOG and the tutorial doc are updated.

## Defects
None.

## Process Gaps
None.

## Required Rework
None.
