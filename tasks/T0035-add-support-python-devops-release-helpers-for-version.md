---
id: T0035
owner: "@claude"
session: claude-20261110-77beef
needs: []
branch: task/T0035-add-support-python-devops-release-helpers-for-version
worktree: .plan/work/T0035-add-support-python-devops-release-helpers-for-version
status: active
started_at: "2026-11-10T02:02:48Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 812.4, input: 128, output: 42740, cache_read: 3876218, cache_write: 119714}
work_duration: 418.4
---
# T0035: Add support_python.devops.release helpers for version files, CHANGELOG freezing and reopening, release notes, and GitHub origins

## Goals
Add `support_python.devops.release` with stdlib-only helpers for version files, CHANGELOG headings, release notes, and GitHub origins.
Consolidate the duplicated logic named in the technical spec, matching the existing behavior.
Leave the scripts unchanged; T0037 rebuilds them on this module.

## Task Execution Steps
- [x] **[Read]**      Read every source implementation listed in the technical spec.
- [x] **[Implement]** Write failing unit tests for every helper in the technical spec's API.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement the release helpers and export them from support_python.devops.
- [x] **[Verify]**    Run the full suite and the integration checks against this repository from the technical spec.
- [x] **[Doc]**       Document the release helpers in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Release logic duplicated across scripts and templates moves into one library module.

- [2026-11-10] **[Verify]**
  Ran the new release tests before implementation; collection failed as expected.
  - Command: ../../../.venv/Scripts/python -m pytest -q tests/test_devops_release.py.
  - ImportError: cannot import name 'VERSION_FILES' from 'support_python.devops'.

- [2026-11-10] **[Implement]**
  Implemented support_python.devops.release and exported its helpers from support_python.devops.
  - Updated tests/test_devops.py, which pins the exact devops __all__ list.
  - VERSION_FILES checks pyproject.toml, gradle.properties, then package.json, per the spec order.

- [2026-11-10] **[Verify]**
  Full suite passed: 813 passed, 3 skipped; ruff check and format clean.
  - Command: ../../../.venv/Scripts/python -m pytest -q, run from the worktree.
  - Integration: read_version and changelog_top_version both returned 2.0.19-pre.
  - Integration: 1.3.5 notes matched extract-release-notes.py output byte for byte via cmp.

- [2026-11-10] **[Doc]**
  Documented the release helpers in README.md and added a v2.0.19-pre CHANGELOG.md entry.
  - New-line Markdown lint is clean; ten remaining issues predate this task.

- [2026-11-10] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF018.

