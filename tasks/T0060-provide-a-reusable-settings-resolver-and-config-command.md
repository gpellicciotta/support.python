---
id: T0060
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T11:41:51Z"
ended_at: "2026-11-10T11:58:08Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@giova"
completion-commit: eb5107fa59fa5545b0ad00c138ba8d5bd8ad94a2
---
# T0060: Provide a reusable settings resolver and config command group in support_python, per the configuration guidelines

## Goals
The dev-guidelines [Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md) define setting precedence, file locations, and a standard `config` command group.
Give tools built on `ToolHarness` both in a few lines: declare the settings once, then resolve them and add `config`.
plan's `plan config` group is the reference behavior for the command shape.

Specifications: [technical-spec.md](T0060-provide-a-reusable-settings-resolver-and-config-command/technical-spec.md).
Completion check: `python -m pytest tests/test_config.py tests/test_config_actions.py` and `ruff check src tests`
Size estimate: 7 files, 700 lines

## Task Execution Steps
- [x] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [x] **[Implement]** Add `Setting` and `SettingsSchema` declarations and a resolver applying the guideline precedence.
- [x] **[Implement]** Add `add_config_actions` registering `path`, `list`, `names`, `get`, `set`, `delete`, and `edit`.
- [x] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [x] **[Doc]**       Add a configuration tutorial under `docs/tutorials/`, update `docs/requirements.md`, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Implement]**
  Added config.py settings resolver and config group, tests, tutorial, requirements, and CHANGELOG entry.
  - 24 tests pass; ruff clean.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @giova.

- [2026-11-10] **[Review]**
  Subagent review fixed findings; review approved by @giova.

- [2026-11-10] **[Verify]**
  Size note: 9 files and about 950 lines, above the typical line, because the resolver, group, tests, and docs ship together.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 9.
  - Lines touched: 950.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

