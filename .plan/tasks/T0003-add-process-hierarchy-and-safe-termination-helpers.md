---
id: T0003
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
# T0003: Add process hierarchy and safe termination helpers

## Goals
Add process helpers to support_python: process hierarchy, start time, liveness with PID-reuse protection, termination, and a protected safe_kill. Sources: plan `core/processes.py` and dev-guidelines `scripts/kill-processes.py`, which each carry a get_process_hierarchy copy; this repo's `scripts/kill-processes.py` is a third. Reconcile the copies into one stdlib-only implementation. Out of scope: plan's task-process tag parsing and evaluate_task_processes.

## Task Execution Steps
- [ ] **[Read]**      Read get_process_hierarchy in plan and in both kill-processes.py copies, and the sibling termination helpers.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement processes.py and re-export its public symbols from the package root.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
