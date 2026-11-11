---
id: T0078
owner: "@claude"
session: claude-20261111-75fdd6
needs: []
branch: task/T0078-add-format-text-json-to-git-repository-backup
worktree: .plan/work/T0078-add-format-text-json-to-git-repository-backup
status: completed
started_at: "2026-11-11T01:39:30Z"
ended_at: "2026-11-11T01:44:53Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 483.0, input: 112, output: 38578, cache_read: 3811432, cache_write: 152206}
  review: {turns: 2, duration_s: 74.4, input: 32, output: 4438, cache_read: 608552, cache_write: 56068}
work_duration: 322.6
review_status: approved
review_round: 1
reviewed_by: "@claude-2"
completion-commit: ecf80fdd1114e9b7961353d2f66288f2a3f2917e
---
# T0078: Add --format text|json to git-repository-backup backup and restore, reporting per-repository results

## Goals
Add `--format text|json` to `git-repository-backup backup` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` with one entry per repository and layer (`mirror`, `archive`) and its outcome, with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Add `--format` to `restore` too, reporting the target, source, and checked-out branch.
Update the hand-written `BackupHarness` help, which lists `--format` for `list` only.

## Task Execution Steps
- [x] **[Read]**      Read the CLI guidelines and the current `backup` handler of `git-repository-backup`.
- [x] **[Implement]** Write failing tests for `git-repository-backup backup --format json`, including `--dry-run` and failure cases.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the JSON document in git-repository-backup.md and add a CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 2 errors; pending fix turn 1 of 2.
  - TF018.
  - TF020.

- [2026-11-11] **[Read]**
  Read the CLI guidelines and the backup and restore handlers of git-repository-backup.

- [2026-11-11] **[Implement]**
  Wrote nine failing tests for backup and restore with --format json, including dry-run and failure cases.

- [2026-11-11] **[Verify]**
  Recorded the red-phase failures in validation-proof.md.

- [2026-11-11] **[Implement]**
  Collected per-repository results in run_backup and a report in run_restore, emitted through emit_json.

- [2026-11-11] **[Verify]**
  Fast suite and slow git-repository-backup tests passed; output recorded in validation-proof.md.

- [2026-11-11] **[Doc]**
  Documented the JSON output in git-repository-backup.md and added a CHANGELOG.md entry.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 approved by @claude-2: Approved.
  - Findings: [review-findings-1.md](T0078-add-format-text-json-to-git-repository-backup/review-findings-1.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

