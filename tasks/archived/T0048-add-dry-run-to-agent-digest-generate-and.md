---
id: T0048
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T09:16:35Z"
ended_at: "2026-11-10T09:25:02Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-code-subagent"
completion-commit: 43df589b715f77fcd4cc86a9cfe25e2105419d3e
---
# T0048: Add --dry-run to agent-digest generate and --format text|json to agent-digest check, as ADR-0003 requires

## Goals
Add --dry-run to agent-digest generate and --format text|json to agent-digest check, as ADR-0003 requires.

## Task Execution Steps
- [x] **[Read]**      Read action_generate, action_check, DigestHarness, and the shared JSON mode from T0053.
- [x] **[Implement]** Write failing dry-run and JSON check tests in tests/tools/test_agent_digest.py.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Add generate --dry-run and check --format with the issue-collecting JSON document.
- [x] **[Verify]**    Run the full suite, ruff, and the installed integration checks from the technical spec.
- [x] **[Doc]**       Update docs/tools/agent-digest.md and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  Use the shared JSON output mode from T0053 for check --format json instead of a tool-specific logger.

- [2026-11-10] **[Verify]**
  Red phase failed eight new tests; full suite, ruff, and installed check/dry-run scenarios pass.
  - Added two end-to-end tests for the installed integration scenarios.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-subagent.

- [2026-11-10] **[Review]**
  Agent reviewer approved round 1; applied the json_output nit for direct action_check calls.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 4.
  - Lines touched: 402.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

