---
id: T0001
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0001: Add atomic text write helpers with Windows-safe retries

## Goals
Add atomic text write helpers to support_python, extracted from the plan project's `utils/common.py`. Writes go through a temporary sibling file, so readers never see a partial file. Windows rename and read locks are retried with backoff. Keep the plan-specific write-journal indirection out of the library.

## Task Execution Steps
- [ ] **[Read]**      Read the plan project's atomic_replace, read_text_retrying, atomic_write_text, and replace_with_text.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement files.py and re-export its public symbols from the package root.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
