---
id: T0029
owner: "@gemini"
session: antigravity-20261109-b2120f
needs: []
branch: task/T0029-align-agent-files-with-adr-0003-canonical-sync
worktree: .plan/work/T0029-align-agent-files-with-adr-0003-canonical-sync
status: completed
started_at: "2026-11-09T22:22:36Z"
ended_at: "2026-11-09T23:24:05Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 8, duration_s: 6187.4, input: 1742992, output: 303220, cache_read: 33318614}
  review: {turns: 4, duration_s: 943.8, input: 36, output: 11074, cache_read: 1219036, cache_write: 13832}
work_duration: 3688.7
review_status: approved
review_round: 2
reviewed_by: "@claude"
completion-commit: 203bf3a279f1cb81af23cb4fd231a363ce3e90e1
---
# T0029: Align agent-files with ADR-0003: canonical sync and check verbs, JSON list output, and .agent-files.json with legacy fallback

## Goals
Make `list`, `sync`, `check`, and `review` the canonical agent-files actions, removing the `update` and `diff` names and alias mapping.
Make `check` read-only, exiting 1 when any tool has pending changes.
Add `--format text|json` to `list` and `check`.
Read project config from `.agent-files.json`, falling back to `agent-files.json` with a warning.
Fix the stale help examples.

## Task Execution Steps
- [x] **[Read]**      Read the agent-files action registration, alias mapping, list and diff output, and config lookup.
- [x] **[Implement]** Write failing tests for verbs, check exit codes, JSON output, config names, and help examples.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Rename the actions, add --format, and add the config fallback in tools/agent_files_config.py.
- [x] **[Verify]**    Run the full suite and the installed integration commands from the technical spec.
- [x] **[Doc]**       Update docs/tools/agent-files.md, README.md, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. It absorbs cancelled T0022's verb and naming goals.

- [2026-11-09] **[Verify]**
  Verified red-phase failures for canonical verbs, JSON output, and .agent-files.json discovery.
  - 17 failed, 87 passed in tests/tools/test_agent_files.py.

- [2026-11-09] **[Implement]**
  Made sync and check canonical, added --format text|json to list and check, and added .agent-files.json discovery with legacy fallback.

- [2026-11-09] **[Verify]**
  Recorded task outcomes. Size note: 481 lines across 6 files keeps the coupled verb, JSON format, and config fallback changes in one self-contained commit.
  - Files touched: 6.
  - Lines touched: 481.
  - Reopenings: 0.

- [2026-11-09] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-09] **[Doc]**
  Updated docs/tools/agent-files.md, README.md, and CHANGELOG.md for canonical sync/check verbs, --format text|json, and .agent-files.json discovery.

- [2026-11-09] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-09] **[Review]**
  Round 1 rejected by @claude: Most goals are met.
  - Findings: [review-findings-1.md](T0029-align-agent-files-with-adr-0003-canonical-sync/review-findings-1.md).

- [2026-11-10] **[Verify]**
  Verified 710 passed in pytest and updated task outcomes. Size note: 565 lines across 7 files includes updating internal unit test calls from update/diff to sync/check across test_agent_files.py.
  - Files touched: 7.
  - Lines touched: 565.
  - Reopenings: 0.

- [2026-11-10] **[Implement]**
  Addressed round 1 review findings: unified check logic, emitted unavailable status on invalid targets, aligned pyproject.toml version, removed legacy verb branches, routed legacy warnings to --log-file, and dropped duplicate JSON keys (TF020 fixed via [Doc] log).

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude: Approved.
  - Findings: [review-findings-2.md](T0029-align-agent-files-with-adr-0003-canonical-sync/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

