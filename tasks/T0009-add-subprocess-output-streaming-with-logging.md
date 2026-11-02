---
id: T0009
owner: ~
needs: ['T0005']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0009: Add subprocess output streaming with logging

## Goals
Add subprocess output streaming to support_python, extracted from plan's `stream_subprocess` and dev-guidelines' `run_step_command`. Stream a child's merged stdout and stderr line by line to a CliLogger, log the command and PID, and return the exit code. Terminate the child on KeyboardInterrupt (terminate, wait 5 seconds, then kill). Agent-specific parsing (rate-limit detection, JSON events) becomes an optional per-line callback. Reconcile with the existing run_step.

## Task Execution Steps
- [ ] **[Read]**      Read stream_subprocess, run_step_command, and devops.run_step; list overlapping behavior and callers' needs.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement the streaming helper, and have run_step reuse it if the behaviors match.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
