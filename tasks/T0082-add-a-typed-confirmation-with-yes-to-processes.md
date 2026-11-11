---
id: T0082
owner: "@claude"
session: claude-20261111-989ee9
needs: []
branch: task/T0082-add-a-typed-confirmation-with-yes-to-processes
worktree: .plan/work/T0082-add-a-typed-confirmation-with-yes-to-processes
status: active
started_at: "2026-11-11T00:45:54Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 368.6, input: 120, output: 20496, cache_read: 3221288, cache_write: 106998}
work_duration: 175.7
review_status: pending
review_round: 1
---
# T0082: Add a typed confirmation with --yes to processes kill, or document why it is exempt from that CLI rule

## Goals
The CLI guidelines require a typed confirmation, skippable with `--yes`, before destructive actions.
`processes kill` terminates processes without asking, and agents and scripts call it non-interactively.
The user decided that `kill` fully complies: it asks for a typed confirmation, and `--yes` skips it.
Non-interactive callers without `--yes` fail with exit code 2 instead of killing; `--dry-run` never asks.
Document the behavior in processes.md.

## Task Execution Steps
- [x] **[Decided]**   Typed confirmation, skippable with `--yes`; no exemption (decided by user).
- [x] **[Implement]** Write failing tests for the chosen behavior, including `--yes` and non-terminal `stdin`.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Implement the chosen confirmation behavior in the `processes kill` handler.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Update processes.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decided]**
  User decided kill requires typed confirmation or --yes, per CLI guidelines.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Implement]**
  Wrote failing tests for --yes, non-terminal stdin, typed confirmation, and dry-run.

- [2026-11-11] **[Verify]**
  Red phase: 3 of 4 new tests failed as expected; recorded in validation-proof.md.

- [2026-11-11] **[Implement]**
  Added typed confirmation and --yes to the processes kill handler; non-terminal stdin without --yes exits 2.

- [2026-11-11] **[Verify]**
  Fast suite 1130 passed; slow processes tests passed with PYTHONPATH=src; ruff clean.

- [2026-11-11] **[Doc]**
  Updated processes.md, migration-v2.md, and CHANGELOG.md.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

