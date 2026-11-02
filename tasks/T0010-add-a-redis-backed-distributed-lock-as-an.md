---
id: T0010
owner: ~
needs: [T0006]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0010: Add a Redis-backed distributed lock as an optional extra

## Goals
Add RedisLock to support_python, extracted from the plan project's `utils/locking.py`. It uses atomic SET NX PX with a UUID token and a Lua compare-and-delete release, with retry jitter. The redis package is an optional extra imported lazily; the core library stays dependency-free. Extend the T0006 factory with redis:// and rediss:// URLs.

## Task Execution Steps
- [ ] **[Read]**      Read plan's RedisLock, its re-entrancy keys, and the redis extra declaration in plan's pyproject.toml.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement RedisLock, the optional redis extra in pyproject.toml, and the factory scheme.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
