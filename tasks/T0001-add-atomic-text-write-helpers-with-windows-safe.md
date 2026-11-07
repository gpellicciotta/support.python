---
id: T0001
owner: "@gemini"
session: antigravity-20261107-d7f2d8
needs: []
branch: task/T0001-add-atomic-text-write-helpers-with-windows-safe
worktree: .plan/work/T0001-add-atomic-text-write-helpers-with-windows-safe
status: active
started_at: "2026-11-07T12:57:01Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 1521.6, input: 351296, output: 67132, cache_read: 7551192}
work_duration: 709.8
review_status: pending
review_round: 1
---
# T0001: Add atomic text write helpers with Windows-safe retries

## Goals
Add atomic text write helpers to support_python, extracted from the plan project's `utils/common.py`. Writes go through a temporary sibling file, so readers never see a partial file. Windows rename and read locks are retried with backoff. Keep the plan-specific write-journal indirection out of the library.

## Task Execution Steps
- [x] **[Read]**      Read the plan project's atomic_replace, read_text_retrying, atomic_write_text, and replace_with_text.
- [x] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [x] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [x] **[Implement]** Implement files.py and re-export its public symbols from the package root.
- [x] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [x] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-07] **[Read]**
  Reviewed atomic_replace, read_text_retrying, atomic_write_text, and replace_with_text in plan/src/plan/utils/common.py.

- [2026-11-07] **[Implement]**
  Authored unit and integration tests for atomic_replace, read_text_retrying, and atomic_write_text in tests/test_files.py.

- [2026-11-07] **[Verify]**
  Executed pytest on tests/test_files.py before implementation and confirmed red-phase ImportError failure.

- [2026-11-07] **[Implement]**
  Implemented atomic_replace, read_text_retrying, and atomic_write_text in src/support_python/files.py and re-exported them from the package root.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md, pyproject.toml, README.md, CLAUDE.md, and docs/index.md for v1.0.9-pre and files.py helpers.

- [2026-11-07] **[Verify]**
  Verified test_files.py, version and CLI tests, and ruff checks. Recorded task outcomes.
  - Files touched: 8.
  - Lines touched: 386.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

