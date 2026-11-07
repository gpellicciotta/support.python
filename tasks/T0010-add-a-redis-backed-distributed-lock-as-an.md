---
id: T0010
owner: "@gemini"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-07T09:42:46Z"
ended_at: "2026-11-07T09:47:20Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-code"
completion-commit: 9ca5c7c634a8cf6bba1704ffbcc76152126386c2
---
# T0010: Add a Redis-backed distributed lock as an optional extra

## Goals
Add RedisLock to support_python, extracted from the plan project's `utils/locking.py`. It uses atomic SET NX PX with a UUID token and a Lua compare-and-delete release, with retry jitter. The redis package is an optional extra imported lazily; the core library stays dependency-free. Extend the T0006 factory with redis:// and rediss:// URLs.

## Task Execution Steps
- [x] **[Read]**      Read plan's RedisLock, its re-entrancy keys, and the redis extra declaration in plan's pyproject.toml.
- [x] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [x] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [x] **[Implement]** Implement RedisLock, the optional redis extra in pyproject.toml, and the factory scheme.
- [x] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [x] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-07] **[Read]**
  Read plan's RedisLock implementation, Lua release script, and redis extra declaration in pyproject.toml.

- [2026-11-07] **[Implement]**
  Authored unit and integration tests in tests/test_locking_redis.py.

- [2026-11-07] **[Verify]**
  Ran tests/test_locking_redis.py and confirmed collection failure before implementation.

- [2026-11-07] **[Implement]**
  Implemented RedisLock, redis extra in pyproject.toml, and factory support for redis:// and rediss://.

- [2026-11-07] **[Verify]**
  Verified tests in test_locking_redis.py pass and ruff check and format are clean.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md, README.md, CLAUDE.md, and docs/index.md with RedisLock documentation.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 approved by @claude-code.

- [2026-11-07] **[Complete]**
  Task completed successfully.

