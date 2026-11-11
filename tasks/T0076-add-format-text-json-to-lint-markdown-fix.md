---
id: T0076
owner: "@claude"
session: claude-20261111-2bc682
needs: []
branch: task/T0076-add-format-text-json-to-lint-markdown-fix
worktree: .plan/work/T0076-add-format-text-json-to-lint-markdown-fix
status: active
started_at: "2026-11-11T01:31:34Z"
ended_at: —
review: agent
preview: none
protocol: standard
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
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
