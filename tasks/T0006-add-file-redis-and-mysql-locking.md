---
id: T0006
owner: "@gemini"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-07T08:55:58Z"
ended_at: "2026-11-07T09:42:28Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 2
reviewed_by: "@claude-code"
completion-commit: 59ac68d81999db10b123d72a2c9bbe60f32de737
---
# T0006: Add the locking base class, file lock, null lock, and backend factory

## Goals
Add the locking base to support_python, extracted from the plan project's `utils/locking.py`: the Lock ABC, LockTimeoutError, FileLock, NullLock, and a backend factory. The factory maps a backend string to a lock ('null', 'file', redis://, mysql://) without reading plan's config tiers. Redis and MySQL locks are separate tasks that need this one.

## Task Execution Steps
- [x] **[Read]**      Read plan's Lock, FileLock, NullLock, and plan_lock; note the re-entrancy and holder-diagnostics behavior.
- [x] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [x] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [x] **[Implement]** Implement locking.py and re-export its public symbols from the package root.
- [x] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [x] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-07] **[Implement]**
  Added locking.py with Lock, FileLock, NullLock, create_lock, tests, exports, and docs.
  - 15 locking tests pass.
  - Full suite: 428 passed.

- [2026-11-07] **[Decided]**
  Redis and MySQL URLs raise NotImplementedError until T0010 and T0011 land.

- [2026-11-07] **[Verify]**
  Recorded task outcomes.
  - Files touched: 7.
  - Lines touched: 450.
  - Reopenings: 0.

- [2026-11-07] **[Read]**
  Read plan's Lock, FileLock, NullLock, and plan_lock; ported re-entrancy and holder diagnostics.

- [2026-11-07] **[Review]**
  Review subagent rejected a corrupted README section; fixed, then approved.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 approved by @claude-code.

- [2026-11-07] **[Review]**
  Claude Code reviewed worktree implementation and recorded approval verdict.

- [2026-11-07] **[Review]**
  Round 2 requested (mode: agent); the work changed after the round 1 approval of commit bfa1eef.

- [2026-11-07] **[Review]**
  Round 2 approved by @claude-code.

- [2026-11-07] **[Complete]**
  Task completed successfully.

