---
id: T0005
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
# T0005: Unify the CLI logger and action harness with dev-guidelines and plan

## Goals
Unify the CLI logger and action harness: bring the generic features of dev-guidelines' ToolLogger and ToolHarness, and plan's TeeLogger, into CliLogger and cli.py. Features: registered actions with handlers, fallback action, exit-code table, startup and exit banners, log-level resolution, build-metadata version suffix. Out of scope: plan's agent stream formatting (JsonStreamLogger, StreamOutputFormatter). Switching consumers over is a follow-up.

## Task Execution Steps
- [ ] **[Read]**      Diff CliLogger, build_action_parser, ToolLogger, ToolHarness, and TeeLogger; list each behavior to keep, merge, or drop.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement the merged logger and harness in logging.py and cli.py, keeping the existing public API compatible.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
