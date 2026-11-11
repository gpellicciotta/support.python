---
id: T0074
owner: "@claude"
session: claude-20261111-e56b1a
needs: []
branch: task/T0074-add-format-text-json-to-processes-kill-reporting
worktree: .plan/work/T0074-add-format-text-json-to-processes-kill-reporting
status: completed
started_at: "2026-11-11T00:50:36Z"
ended_at: "2026-11-11T00:56:11Z"
review: agent
preview: none
protocol: adhoc
usage:
  worker: {turns: 6, duration_s: 417.2, input: 136, output: 25846, cache_read: 3693360, cache_write: 119674}
  review: {turns: 4, duration_s: 102.8, input: 44, output: 7162, cache_read: 769256, cache_write: 113032}
work_duration: 334.9
review_status: approved
review_round: 2
reviewed_by: "@claude-2"
completion-commit: 955b3a6d30bb5c7d138951ce6a9ea454a63a28ac
---
# T0074: Add --format text|json to processes kill, reporting each killed, skipped, and failed PID

## Goals
Add `--format text|json` to `processes kill` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` listing each PID with its outcome (`killed`, `skipped-protected`, `not-found`, or `failed`), with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Report `would-kill` and `would-skip-protected` outcomes for `--dry-run`.

## Task Execution Steps
- [x] **[Read]**      Read the CLI guidelines and the current `kill` handler of `processes`.
- [x] **[Implement]** Write failing tests for `processes kill --format json`, including `--dry-run` and failure cases.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the JSON document in processes.md and add a CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 2 errors; pending fix turn 1 of 2.
  - TF018.
  - TF020.

- [2026-11-11] **[Read]**
  Read the CLI guidelines and the kill handler of processes.

- [2026-11-11] **[Implement]**
  Wrote three failing tests for kill --format json, including dry-run and failure cases.

- [2026-11-11] **[Verify]**
  Red phase: the three new tests failed against the old source; see validation-proof.md.

- [2026-11-11] **[Implement]**
  Added safe_kill_report and emitted per-PID results with emit_json in json mode.

- [2026-11-11] **[Verify]**
  Fast suite passed with 1133 tests; slow processes tests passed; output in validation-proof.md.

- [2026-11-11] **[Doc]**
  Documented the JSON document in processes.md and added CHANGELOG entries.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 rejected by @claude-2: The implementation is clean and well tested: `safe_kill_report`, the dry-run outcomes, docs, and CHANGELOG are in place.
  - Findings: [review-findings-1.md](T0074-add-format-text-json-to-processes-kill-reporting/review-findings-1.md).

- [2026-11-11] **[Implement]**
  Addressed review round 1: json mode now sends the kill confirmation to stderr, with a test and docs.

- [2026-11-11] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 2 approved by @claude-2: The round 1 defect is fixed: in `json` mode `run_kill` redirects the confirmation summary and prompt to `stderr`, with a.
  - Findings: [review-findings-2.md](T0074-add-format-text-json-to-processes-kill-reporting/review-findings-2.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

