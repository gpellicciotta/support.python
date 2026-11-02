---
id: T0006
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
# T0006: Add the locking base class, file lock, null lock, and backend factory

## Goals
Add the locking base to support_python, extracted from the plan project's `utils/locking.py`: the Lock ABC, LockTimeoutError, FileLock, NullLock, and a backend factory. The factory maps a backend string to a lock ('null', 'file', redis://, mysql://) without reading plan's config tiers. Redis and MySQL locks are separate tasks that need this one.

## Task Execution Steps
- [ ] **[Read]**      Read plan's Lock, FileLock, NullLock, and plan_lock; note the re-entrancy and holder-diagnostics behavior.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement locking.py and re-export its public symbols from the package root.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
