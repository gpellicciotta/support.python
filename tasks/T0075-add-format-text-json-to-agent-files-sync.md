---
id: T0075
owner: ~
needs: [T0070]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0075: Add --format text|json to agent-files sync, reporting each tool's planned and applied changes

## Goals
Add `--format text|json` to `agent-files sync` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` listing each tool with its instruction-file and skill changes, planned or applied, with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Reuse the document shape of `check --format json` where the data overlaps.

## Task Execution Steps
- [ ] **[Read]**      Read the CLI guidelines and the current `sync` handler of `agent-files`.
- [ ] **[Implement]** Write failing tests for `agent-files sync --format json`, including `--dry-run` and failure cases.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document the JSON document in agent-files.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
