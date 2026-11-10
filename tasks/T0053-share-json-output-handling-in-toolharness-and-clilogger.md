---
id: T0053
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T08:58:05Z"
ended_at: "2026-11-10T09:16:20Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 2
reviewed_by: "@claude-code-subagent"
completion-commit: af1cb8830649a6140b06fe685cb0738154708769
---
# T0053: Share JSON output handling in ToolHarness and CliLogger, and use it in agent-files, lint-markdown, processes, and git-repository-backup

## Goals
Add one shared JSON output mode to `CliLogger` and `ToolHarness`, so stdout carries only the JSON document while every log message still reaches stderr.
Enable it automatically when an action's `--format` option is `json`, and add a shared helper that registers that option.
Replace the per-tool implementations in agent-files, lint-markdown, processes, and git-repository-backup with the shared mode.
Keep each tool's JSON documents byte-for-byte unchanged.

## Task Execution Steps
- [x] **[Read]**      Read StderrRoutingLogger, _JsonAwareLogger, JsonModeLogger, the backup harness overrides, and ToolHarness logger hooks.
- [x] **[Implement]** Write failing tests for the shared JSON mode in tests/test_cli.py and tests/test_logging.py.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement the shared JSON mode, format option helper, and emit_json in logging.py and cli.py.
- [x] **[Implement]** Switch the four tools to the shared mode and delete their private JSON loggers and overrides.
- [x] **[Verify]**    Run the full suite and the installed integration checks from the technical spec.
- [x] **[Doc]**       Update CHANGELOG.md and the four docs/tools pages for the unified stderr behavior.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  Requested by the user on 2026-11-10; four tools each carried their own JSON stdout handling with diverging stderr behavior.

- [2026-11-10] **[Verify]**
  Full suite, ruff, installed JSON-mode checks, and before/after stdout comparison pass.
  - Undeclared: tests/tools/test_agent_files.py, three docs/tools pages, CLI tutorial.

- [2026-11-10] **[Doc]**
  Size note: 14 counted files, 477 lines; above the typical line because four private copies are replaced.
  - agent_files logger.log calls rewritten by a scratch AST script, counted as hand-edited.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude-code-subagent: CHANGELOG names the wrong tools whose JSON-mode INFO lines changed; processes was unchanged, git-repository-backup changed.

- [2026-11-10] **[Review]**
  Fixed round-1 rejection: CHANGELOG now names the tools whose JSON-mode INFO lines changed; added emit docstring note and tidied tutorial.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude-code-subagent.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 14.
  - Lines touched: 482.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

