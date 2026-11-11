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

