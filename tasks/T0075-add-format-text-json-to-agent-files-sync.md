---
id: T0075
owner: "@claude"
session: claude-20261111-4d3ca8
needs: []
branch: task/T0075-add-format-text-json-to-agent-files-sync
worktree: .plan/work/T0075-add-format-text-json-to-agent-files-sync
status: active
started_at: "2026-11-11T01:26:30Z"
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
- [x] **[Read]**      Read the CLI guidelines and the current `sync` handler of `agent-files`.
- [x] **[Implement]** Write failing tests for `agent-files sync --format json`, including `--dry-run` and failure cases.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the JSON document in agent-files.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
