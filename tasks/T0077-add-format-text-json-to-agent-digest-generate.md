---
id: T0077
owner: "@claude"
session: claude-20261111-6038ef
needs: []
branch: task/T0077-add-format-text-json-to-agent-digest-generate
worktree: .plan/work/T0077-add-format-text-json-to-agent-digest-generate
status: active
started_at: "2026-11-11T00:56:31Z"
ended_at: —
review: agent
preview: none
protocol: adhoc
usage:
  worker: {turns: 2, duration_s: 336.2, input: 116, output: 27276, cache_read: 3371936, cache_write: 109496}
work_duration: 180.2
---
# T0077: Add --format text|json to agent-digest generate, reporting written and unchanged digest and skill files

## Goals
Add `--format text|json` to `agent-digest generate` through `ToolHarness.add_format_option`, as the CLI guidelines require.
In `json` mode, print one JSON document on `stdout` listing the digest and each skill file as `created`, `updated`, or `unchanged`, with all log lines on `stderr`.
Keep the exit codes and the `text` output unchanged.
Reuse the status names of `check --format json` where they apply.

## Task Execution Steps
- [x] **[Read]**      Read the CLI guidelines and the current `generate` handler of `agent-digest`.
- [x] **[Implement]** Write failing tests for `agent-digest generate --format json`, including `--dry-run` and failure cases.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Collect per-item results in the handler and emit them with `CliLogger.emit_json` in `json` mode.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the JSON document in agent-digest.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 2 errors; pending fix turn 1 of 2.
  - TF018.
  - TF020.

- [2026-11-11] **[Read]**
  Read the CLI guidelines and the agent-digest generate handler.

- [2026-11-11] **[Implement]**
  Added GenerateJsonFormatTests covering statuses, dry run, and failure cases.

- [2026-11-11] **[Verify]**
  Red phase showed 7 failed, 1 passed before implementation.

- [2026-11-11] **[Implement]**
  Collected per-item results in action_generate and emitted them with emit_json.

- [2026-11-11] **[Verify]**
  Full suite passed with 1142 tests; slow digest tests passed.

- [2026-11-11] **[Doc]**
  Documented the generate JSON output and added a changelog entry.

