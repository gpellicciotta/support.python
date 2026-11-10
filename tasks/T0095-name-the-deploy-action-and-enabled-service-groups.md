---
id: T0095
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T15:28:49Z"
ended_at: "2026-11-10T15:37:00Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 2
reviewed_by: "@codex"
completion-commit: af7f2354791b7ca472b37c66dfc279f9e34bc1d5
---
# T0095: Name the deploy action and enabled service groups in the DevopsCli default description

## Goals
Make the `DevopsCli` default description name `deploy` once `set_deploy` enables it.
Make it name the service groups that `add_services` registers, such as docker, db, and server.
Keep a caller-supplied `description` unchanged; template.python T0014 had to pass one as a workaround.
Completion check: `python scripts/devops.py check`
Size estimate: 3 files, 60 lines

### Declared Files
- src/support_python/devops/cli.py
- tests/test_devops_cli.py
- CHANGELOG.md

### Tests
- Unit: the default description names deploy after `set_deploy`, and the enabled groups after `add_services`.
- Unit: a custom description stays unchanged after both calls.
- Integration test: none (help output is covered by the existing `DevopsCli` help tests in the full suite)

## Task Execution Steps
- [x] **[Implement]** Author the description tests for deploy, service groups, and custom descriptions.
- [x] **[Verify]**    Run the new tests and record their failure output.
- [x] **[Implement]** Rebuild the default description in `set_deploy` and `add_services`.
- [x] **[Verify]**    Run `python scripts/devops.py check` and record the output.
- [x] **[Doc]**       Add the CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @codex: Service-group detection omits groups that replace previously registered actions; add collision and grammar tests.

- [2026-11-10] **[Implement]**
  Fixed review round 1: service groups replacing earlier actions are now detected by action identity, with collision and grammar tests.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @codex: Round 2: identity comparison fixes the collision; no remaining correctness bugs.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 3.
  - Lines touched: 69.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

