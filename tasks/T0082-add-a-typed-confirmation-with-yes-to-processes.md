---
id: T0082
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
# T0082: Add a typed confirmation with --yes to processes kill, or document why it is exempt from that CLI rule

## Goals
The CLI guidelines require a typed confirmation, skippable with `--yes`, before destructive actions.
`processes kill` terminates processes without asking, and agents and scripts call it non-interactively.
Decide with the user whether `kill` asks for confirmation, skips it when `stdin` is not a terminal, or stays exempt.
Implement the chosen behavior, or record the exemption in processes.md.

## Task Execution Steps
- [ ] **[Decide]**    Ask the user which `processes kill` confirmation behavior to adopt.
- [ ] **[Implement]** Write failing tests for the chosen behavior, including `--yes` and non-terminal `stdin`.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Implement the chosen confirmation behavior in the `processes kill` handler.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Update processes.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
