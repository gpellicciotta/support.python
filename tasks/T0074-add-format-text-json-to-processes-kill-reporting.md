---
id: T0074
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
# T0074: Add --format text|json to processes kill, reporting each killed, skipped, and failed PID

## Goals
Add `--format text|json` to `processes kill` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` listing each PID with its outcome (`killed`, `skipped-protected`, `not-found`, or `failed`), with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Report `would-kill` and `would-skip-protected` outcomes for `--dry-run`.

## Task Execution Steps
- [ ] **[Read]**      Read the CLI guidelines and the current `kill` handler of `processes`.
- [ ] **[Implement]** Write failing tests for `processes kill --format json`, including `--dry-run` and failure cases.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document the JSON document in processes.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
