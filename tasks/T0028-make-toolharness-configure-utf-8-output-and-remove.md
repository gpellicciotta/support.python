---
id: T0028
owner: "@gemini"
session: antigravity-20261109-879abf
needs: []
branch: task/T0028-make-toolharness-configure-utf-8-output-and-remove
worktree: .plan/work/T0028-make-toolharness-configure-utf-8-output-and-remove
status: active
started_at: "2026-11-09T21:54:03Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 1647.0, input: 546764, output: 52940, cache_read: 17392998}
  review: {turns: 2, duration_s: 343.6, input: 52, output: 14956, cache_read: 1223546, cache_write: 88034}
review_status: rejected
review_round: 1
reviewed_by: "@claude"
work_duration: 1012.1
---
# T0028: Make ToolHarness configure UTF-8 output for every tool, and remove the ToolLogger and TeeLogger logger aliases.

## Goals
Make `ToolHarness.run` call `configure_utf8_output()` before parsing, and delete the per-tool UTF-8 reconfiguration blocks.
Remove the `ToolLogger` and `TeeLogger` aliases from `support_python.logging` and the package root.
Replace every remaining alias use with `CliLogger` through the mechanical command in the technical spec.

## Task Execution Steps
- [x] **[Read]**      Read ToolHarness.run, configure_utf8_output, every stream reconfiguration block, and every alias use.
- [x] **[Implement]** Write failing tests for harness UTF-8 setup and the absence of both logger aliases.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Run the alias sweep, delete the aliases, and move UTF-8 setup into ToolHarness.run.
- [x] **[Verify]**    Run ruff, the full suite, and each installed console script's help action.
- [x] **[Doc]**       Update README.md and CHANGELOG.md, listing the removed aliases as breaking changes.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. UTF-8 setup belongs in ToolHarness; the logger aliases go in the breaking release.

- [2026-11-09] **[Read]**
  Read ToolHarness.run, configure_utf8_output, per-tool stream reconfiguration blocks, and all ToolLogger and TeeLogger alias usages.

- [2026-11-09] **[Implement]**
  Authored failing unit and integration tests for ToolHarness UTF-8 configuration, tool stream reconfiguration removal, and absence of ToolLogger and TeeLogger aliases.

- [2026-11-09] **[Verify]**
  Ran new unit tests and verified red-phase failures for UTF-8 setup, tool stream reconfiguration, and logger aliases.

- [2026-11-09] **[Implement]**
  Ran mechanical alias sweep, removed ToolLogger and TeeLogger aliases, and moved configure_utf8_output into ToolHarness.run.

- [2026-11-09] **[Verify]**
  Ran ruff check, the full pytest suite (705 passed), and all four console script help actions.

- [2026-11-09] **[Doc]**
  Updated README.md and CHANGELOG.md with breaking change note for removed ToolLogger and TeeLogger aliases and ToolHarness UTF-8 setup.

- [2026-11-09] **[Verify]**
  Recorded task outcomes.
  - Files touched: 17.
  - Lines touched: 267.
  - Reopenings: 0.

- [2026-11-09] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-09] **[Review]**
  Round 1 rejected by @claude: The core change is correct and well tested.
  - Findings: [review-findings-1.md](T0028-make-toolharness-configure-utf-8-output-and-remove/review-findings-1.md).

- [2026-11-09] **[Implement]**
  Fixed duplicated CliLogger prose in processes.py, removed alias mentions in CLAUDE.md and docs/index.md, and renamed the agent_files subclass to StderrRoutingLogger.

- [2026-11-09] **[Doc]**
  Recorded the 6 extra sweep-touched files and the python -c cp1252-pipe integration test mechanism in technical-spec.md.

- [2026-11-09] **[Verify]**
  Recorded updated task outcomes after review rework.
  - Files touched: 17.
  - Lines touched: 267.
  - Reopenings: 0.

