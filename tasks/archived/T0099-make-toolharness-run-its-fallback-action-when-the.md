---
id: T0099
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T16:41:09Z"
ended_at: "2026-11-10T16:54:48Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 3
reviewed_by: "@codex"
completion-commit: ebb8fd53b2242a83dcf25fa7f59ab08d12519176
---
# T0099: Make ToolHarness run its fallback action when the command line starts with an option, moving run_capture_cli's reordering into the harness

## Goals
Make `ToolHarness` run its fallback action when the command line starts with an option, as in `tool --url x`.
Keep a named action after leading options, as in `tool --verbose list`, and keep `help` and `version` working there.
Move the reordering out of `run_capture_cli` into the harness, keeping capture behavior unchanged.
todos.server smoke-test and counters.server test-ui need this to keep their leading-option calls.
Completion check: `python scripts/devops.py check`
Size estimate: 6 files, 90 lines

### Declared Files
- src/support_python/cli.py
- src/support_python/capture.py
- tests/test_cli.py
- docs/tutorials/cli-harness-and-logging.md
- docs/migration-v2.md
- CHANGELOG.md

### Tests
- Unit: a fallback harness runs its fallback for `--target staging`, and keeps `run`, `version`, and `help` after leading options.
- Unit: a harness without a fallback still exits 2 for a leading unknown option.
- Integration: the existing `run_capture_cli` leading-option tests pass unchanged on the moved logic.

## Task Execution Steps
- [x] **[Implement]** Author harness tests for leading options with and without a fallback action.
- [x] **[Verify]**    Run the new tests and record their failure output.
- [x] **[Implement]** Move the reordering from `run_capture_cli` into `ToolHarness.run`.
- [x] **[Verify]**    Run `python scripts/devops.py check` and record the output.
- [x] **[Doc]**       Update the harness tutorial, migration-v2.md, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @codex: Leading-option scanner miscounts nargs='?' values, ignores other actions' options, and breaks targeted help after global values.

- [2026-11-10] **[Implement]**
  Fixed review round 1: arities come from all action parsers, optional values skip action names, and help keeps its target.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 rejected by @codex: Leading-option scan misses argparse long-option abbreviations and bundled short options with separate values.

- [2026-11-10] **[Implement]**
  Fixed review round 2: the scan resolves unique long-option prefixes and bundled short options as argparse does.

- [2026-11-10] **[Review]**
  Round 3 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 3 approved by @codex: Round 3: no blocking findings; cross-action abbreviation ambiguity noted as non-blocking.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 6.
  - Lines touched: 142.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

