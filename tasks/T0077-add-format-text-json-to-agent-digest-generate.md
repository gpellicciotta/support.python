---
id: T0077
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
# T0077: Add --format text|json to agent-digest generate, reporting written and unchanged digest and skill files

## Goals
Add `--format text|json` to `agent-digest generate` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` listing the digest and each skill file as `created`, `updated`, or `unchanged`, with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Reuse the status names of `check --format json` where they apply.

## Task Execution Steps
- [ ] **[Read]**      Read the CLI guidelines and the current `generate` handler of `agent-digest`.
- [ ] **[Implement]** Write failing tests for `agent-digest generate --format json`, including `--dry-run` and failure cases.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document the JSON document in agent-digest.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
