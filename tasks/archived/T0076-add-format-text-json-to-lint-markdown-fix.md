---
id: T0076
owner: "@claude"
session: claude-20261111-2bc682
needs: []
branch: task/T0076-add-format-text-json-to-lint-markdown-fix
worktree: .plan/work/T0076-add-format-text-json-to-lint-markdown-fix
status: completed
started_at: "2026-11-11T01:31:34Z"
ended_at: "2026-11-11T01:39:10Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 6, duration_s: 531.2, input: 156, output: 32586, cache_read: 5258532, cache_write: 147448}
  review: {turns: 4, duration_s: 228.4, input: 56, output: 9344, cache_read: 1068076, cache_write: 118972}
work_duration: 455.4
review_status: approved
review_round: 2
reviewed_by: "@claude-2"
completion-commit: 2cc0fcceeb63eb5831339b91396077aad05f2acf
---
# T0076: Add --format text|json to lint-markdown fix, reporting fixed files and remaining issues

## Goals
Add `--format text|json` to `lint-markdown fix` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` listing each fixed file with its fixes and every remaining issue, with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Reuse the issue objects of `check --format json`.

## Task Execution Steps
- [x] **[Read]**      Read the CLI guidelines and the current `fix` handler of `lint-markdown`.
- [x] **[Implement]** Write failing tests for `lint-markdown fix --format json`, including `--dry-run` and failure cases.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the JSON document in lint-markdown.md and add a CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read the CLI guidelines and the lint-markdown run_lint handler.

- [2026-11-11] **[Implement]**
  Wrote failing tests for fix --format json, dry-run, empty, and failure cases.

- [2026-11-11] **[Verify]**
  Ran the new tests; five failed and one help test failed because fix lacked --format.
  - Red-phase output recorded in validation-proof.md.

- [2026-11-11] **[Implement]**
  Collected per-file fixes in run_lint and emitted them with emit_json in json mode.

- [2026-11-11] **[Verify]**
  Full suite passed: 1195 passed, 5 skipped; ruff clean; integration run exited 1 with valid JSON.

- [2026-11-11] **[Doc]**
  Documented the fix JSON document in lint-markdown.md and added a CHANGELOG entry.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 rejected by @claude-2: The implementation is correct and meets the goals.
  - Findings: [review-findings-1.md](T0076-add-format-text-json-to-lint-markdown-fix/review-findings-1.md).

- [2026-11-11] **[Implement]**
  Addressed review round 1: snake_case JSON keys matching check, removed duplicate separator.

- [2026-11-11] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 2 approved by @claude-2: The work meets the task goals.
  - Findings: [review-findings-2.md](T0076-add-format-text-json-to-lint-markdown-fix/review-findings-2.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

