---
id: T0079
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
# T0079: Show every action's options in ToolHarness help --verbose, with metavars and consistent help text

## Goals
Make `ToolHarness` `help --verbose` list each action's own options, with metavars, under its detailed description.
Show metavars such as `PATH` and `PID` in per-action option rows, which now show bare flags like `--cwd`.
Start every option description lowercase, matching the standard option rows.
Apply the change to every tool built on `ToolHarness`, including `DevopsCli`.
List positional arguments with their help text too; template.python's T0015 had to describe them in `detail=`.

## Task Execution Steps
- [ ] **[Read]**      Read the CLI guidelines and the help rendering in cli.py.
- [ ] **[Implement]** Write failing tests for action options and metavars in `help --verbose` and per-action help.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Render action options from each action parser, with metavars, in `ToolHarness.format_help`.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Verify]**    Run `help --verbose` for all five tools and `devops.py`, recording the output.
- [ ] **[Doc]**       Update cli-harness-and-logging.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
