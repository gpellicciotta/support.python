---
id: T0008
owner: ~
needs: ['T0004']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0008: Add a task rate limiter

## Goals
Add a sliding-window rate limiter to support_python, extracted from the plan project's `utils/rate_limiter.py`. Scope: TaskRateLimiter with is_enabled, prune, can_dispatch, get_wait_duration, and record_dispatch. Out of scope: format_rate_limit_info, which formats agent-specific data. Wait-duration text may reuse the duration helpers from T0004.

## Task Execution Steps
- [ ] **[Read]**      Read plan's TaskRateLimiter and its callers' expectations of the 1-second minimum wait.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement ratelimit.py and re-export its public symbols from the package root.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
