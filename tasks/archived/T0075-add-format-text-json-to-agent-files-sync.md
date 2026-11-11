---
id: T0075
owner: "@claude"
session: claude-20261111-4d3ca8
needs: []
branch: task/T0075-add-format-text-json-to-agent-files-sync
worktree: .plan/work/T0075-add-format-text-json-to-agent-files-sync
status: completed
started_at: "2026-11-11T01:26:30Z"
ended_at: "2026-11-11T01:31:14Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 394.2, input: 120, output: 27124, cache_read: 3843194, cache_write: 136232}
  review: {turns: 2, duration_s: 85.6, input: 32, output: 3844, cache_read: 610774, cache_write: 59096}
work_duration: 283.9
review_status: approved
review_round: 1
reviewed_by: "@claude-2"
completion-commit: 607f998623a05a46c808938d4f1296cd3255ec21
---
# T0075: Add --format text|json to agent-files sync, reporting each tool's planned and applied changes

## Goals
Add `--format text|json` to `agent-files sync` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` listing each tool with its instruction-file and skill changes, planned or applied, with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Reuse the document shape of `check --format json` where the data overlaps.

## Task Execution Steps
- [x] **[Read]**      Read the CLI guidelines and the current `sync` handler of `agent-files`.
- [x] **[Implement]** Write failing tests for `agent-files sync --format json`, including `--dry-run` and failure cases.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the JSON document in agent-files.md and add a CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read the CLI guidelines, the sync handler, and the check JSON tests.

- [2026-11-11] **[Implement]**
  Wrote four failing sync --format json tests covering apply, dry-run, prune, and failure cases.

- [2026-11-11] **[Verify]**
  Recorded red-phase failures in validation-proof.md: three tests exit 2, text test passes.

- [2026-11-11] **[Implement]**
  Collected per-tool changes in sync handlers and emitted them through emit_json in json mode.

- [2026-11-11] **[Verify]**
  Full suite passed with 1190 tests; slow agent-files tests passed; proof recorded.

- [2026-11-11] **[Doc]**
  Documented the JSON document in agent-files.md and added the CHANGELOG entry.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 approved by @claude-2: Meets all goals.
  - Findings: [review-findings-1.md](T0075-add-format-text-json-to-agent-files-sync/review-findings-1.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

