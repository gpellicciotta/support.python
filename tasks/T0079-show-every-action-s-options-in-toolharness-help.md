---
id: T0079
owner: "@claude"
session: claude-20261111-8a0e75
needs: []
branch: task/T0079-show-every-action-s-options-in-toolharness-help
worktree: .plan/work/T0079-show-every-action-s-options-in-toolharness-help
status: completed
started_at: "2026-11-11T00:39:49Z"
ended_at: "2026-11-11T00:45:34Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 473.4, input: 136, output: 26384, cache_read: 4684086, cache_write: 152458}
  review: {turns: 2, duration_s: 128.6, input: 28, output: 5262, cache_read: 557014, cache_write: 66236}
work_duration: 345.0
review_status: approved
review_round: 1
reviewed_by: "@claude-2"
completion-commit: ee614a70420f6d90d33be379cf4686cece277ccf
---
# T0079: Show every action's options in ToolHarness help --verbose, with metavars and consistent help text

## Goals
Make `ToolHarness` `help --verbose` list each action's own options, with metavars, under its detailed description.
Show metavars such as `PATH` and `PID` in per-action option rows, which now show bare flags like `--cwd`.
Start every option description lowercase, matching the standard option rows.
Apply the change to every tool built on `ToolHarness`, including `DevopsCli`.
List positional arguments with their help text too; template.python's T0015 had to describe them in `detail=`.

## Task Execution Steps
- [x] **[Read]**      Read the CLI guidelines and the help rendering in cli.py.
- [x] **[Implement]** Write failing tests for action options and metavars in `help --verbose` and per-action help.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Render action options from each action parser, with metavars, in `ToolHarness.format_help`.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Verify]**    Run `help --verbose` for all five tools and `devops.py`, recording the output.
- [x] **[Doc]**       Update cli-harness-and-logging.md and add a CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read CLI guidelines and help rendering in cli.py.

- [2026-11-11] **[Implement]**
  Wrote failing tests for action options, metavars, and positionals.

- [2026-11-11] **[Verify]**
  Recorded red-phase failures in validation-proof.md.

- [2026-11-11] **[Implement]**
  Rendered action options and arguments with metavars in format_help and format_action_help; lowercased option help.

- [2026-11-11] **[Verify]**
  Fast suite passed; two slow foreign-venv subtests fail on main too.

- [2026-11-11] **[Verify]**
  Ran help --verbose for all five tools and devops.py.

- [2026-11-11] **[Doc]**
  Updated cli-harness-and-logging.md and CHANGELOG.md.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 approved by @claude-2: Work meets all goals.
  - Findings: [review-findings-1.md](T0079-show-every-action-s-options-in-toolharness-help/review-findings-1.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

