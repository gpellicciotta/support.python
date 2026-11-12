---
id: T0094
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T16:55:06Z"
ended_at: "2026-11-10T16:59:42Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@codex"
completion-commit: 935b7cfe5cb90afa309a0bbc35779f0e2eb39565
---
# T0094: Let run_capture_cli accept app-specific options and pass their values to the capture and tour handlers

## Goals
Let `run_capture_cli` accept app-specific `capture` options and pass their values to the capture handler.
Add a `capture_options` parser hook and a `prepare_capture` arguments hook to `CaptureAppConfig`.
auth's capture-view lost its `--theme` option in T0220 for lack of this hook.
Completion check: `python scripts/devops.py check`
Size estimate: 4 files, 80 lines

### Declared Files
- src/support_python/capture.py
- tests/test_capture.py
- docs/tutorials/view-capture.md
- CHANGELOG.md

### Tests
- Unit: an app `--theme` option reaches `run_capture` as a rewritten `mode`, also after leading options, and shows in help.
- Unit: without the hook, `--theme` still exits 2.
- Integration test: none (the capture engine needs Chrome; handler dispatch is covered by the CLI tests)

## Task Execution Steps
- [x] **[Implement]** Author CLI tests for app-specific capture options with and without the hooks.
- [x] **[Verify]**    Run the new tests and record their failure output.
- [x] **[Implement]** Add the `capture_options` and `prepare_capture` hooks to the capture harness.
- [x] **[Verify]**    Run `python scripts/devops.py check` and record the output.
- [x] **[Doc]**       Document the hooks in view-capture.md and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @codex: No blocking correctness findings.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 4.
  - Lines touched: 61.
  - Reopenings: 0.

- [2026-11-10] **[Implement]**
  Added the capture_options parser hook and the prepare_capture arguments hook to the capture harness.

- [2026-11-10] **[Complete]**
  Task completed successfully.

