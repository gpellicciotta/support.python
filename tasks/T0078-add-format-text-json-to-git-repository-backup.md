---
id: T0078
owner: ~
needs: [T0068]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0078: Add --format text|json to git-repository-backup backup and restore, reporting per-repository results

## Goals
Add `--format text|json` to `git-repository-backup backup` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` with one entry per repository and layer (`mirror`, `archive`) and its outcome, with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Add `--format` to `restore` too, reporting the target, source, and checked-out branch.
Update the hand-written `BackupHarness` help, which lists `--format` for `list` only.

## Task Execution Steps
- [ ] **[Read]**      Read the CLI guidelines and the current `backup` handler of `git-repository-backup`.
- [ ] **[Implement]** Write failing tests for `git-repository-backup backup --format json`, including `--dry-run` and failure cases.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document the JSON document in git-repository-backup.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
