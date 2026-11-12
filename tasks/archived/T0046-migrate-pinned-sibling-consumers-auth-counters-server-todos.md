---
id: T0046
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T14:53:16Z"
ended_at: "2026-11-10T17:03:01Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@codex"
completion-commit: b9320501240a7bc57ce09b9246b6027d08301278
---
# T0046: Migrate pinned sibling consumers (auth, counters.server, todos.server, template.python) off build_action_parser, print_help, and print_version when they upgrade to support-python v2

## Goals
Upgrade auth, counters.server, todos.server, and template.python to the released support-python v2.0.0.
Each project tracks its own upgrade task, which migrates off the removed CLI helpers and patch targets.
This task coordinates them and fixes any support.python gaps the migrations expose.
Completion check: each sibling upgrade task completes with its tests passing against v2.0.0.
Size estimate: 2 files, 40 lines in support.python; sibling diffs count in their own tasks.

### Declared Files
- docs/migration-v2.md
- CHANGELOG.md

### Tests
- Unit test: none (support.python code is unchanged; sibling tasks carry their own unit tests)
- Integration test: none (each sibling task runs its suites against a v2.0.0 install)

## Task Execution Steps
- [x] **[Implement]** Create and run an upgrade task in auth, counters.server, todos.server, and template.python.
- [x] **[Verify]**    Review each sibling diff and its test evidence against support-python v2.0.0.
- [x] **[Doc]**       Record gaps the migrations exposed in migration-v2.md and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Implement]**
  Ran upgrade tasks in auth (T0220), counters.server (T0269, T0271), and todos.server (T0212, T0213); template.python (T0014-T0017) ran in session support-python-9b.

- [2026-11-10] **[Verify]**
  Reviewed each sibling diff, had Codex review each task, and reran every sibling suite against v2.0.0 in its .venv.

- [2026-11-10] **[Doc]**
  Documented .venv installs and changed outputs in migration-v2.md; spun off T0094, T0095, and T0099, and cancelled T0096.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @codex: migration-v2.md claims match v2.0.0 code and the venv prelude snippet is correct.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 2.
  - Lines touched: 30.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

