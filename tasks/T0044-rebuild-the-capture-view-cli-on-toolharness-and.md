---
id: T0044
owner: "@claude"
session: claude-20261110-61f972
needs: []
branch: task/T0044-rebuild-the-capture-view-cli-on-toolharness-and
worktree: .plan/work/T0044-rebuild-the-capture-view-cli-on-toolharness-and
status: active
started_at: "2026-11-10T04:22:23Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 928.4, input: 212, output: 50900, cache_read: 9421398, cache_write: 209810}
  review: {turns: 2, duration_s: 451.6, input: 68, output: 19514, cache_read: 1943372, cache_write: 122996}
review_status: rejected
review_round: 1
reviewed_by: "@claude-2"
work_duration: 708.3
---
# T0044: Rebuild the capture view CLI on ToolHarness, and remove build_action_parser, print_help, print_version, and format_version

## Goals
Rebuild `support_python.capture`'s view-capture CLI (`run_capture_cli` and its parser) on `ToolHarness`, keeping its options, actions, and capture behavior.
Keep the `run_capture_cli(config, argv=None) -> int` signature that consumer scripts call.
Remove `build_action_parser`, `print_help`, `print_version`, and `format_version` from `support_python.cli` and the package root.
Leave `scripts/_cli_common.py` as the stdlib-only copy that `bootstrap-dev-environment.py` uses.

## Task Execution Steps
- [x] **[Read]**      Read run_capture_cli, its parser, its tests, and ../auth/scripts/capture-view.py.
- [x] **[Implement]** Write failing tests for the harness-based capture CLI and the removed argparse helpers.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Rebuild the capture CLI on ToolHarness and delete the four helpers and their exports.
- [x] **[Verify]**    Run the full suite and the capture CLI integration check from the technical spec.
- [x] **[Doc]**       Update README.md and CHANGELOG.md, listing the removed helpers as breaking changes.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. ToolHarness becomes the only CLI API; capture was the last user of the parallel helpers.

- [2026-11-10] **[Decided]**
  Kept STANDARD_CAPTURE_EXIT_CODES and STANDARD_EXIT_CODES; replaced build_capture_parser with build_capture_harness; no arguments now shows help per harness convention.

- [2026-11-10] **[Verify]**
  Full suite passed; auth capture-view.py help failed because auth imports build_capture_parser, print_help, and print_version directly.
  - 1036 passed, 3 skipped.
  - Shim running auth config through run_capture_cli exited 0.
  - Recorded auth backlog task T0217 for migration.

- [2026-11-10] **[Doc]**
  Size note: diff reached 9 files and 572 lines, above the typical line; docs/index.md and docs/requirements.md were undeclared helper references.

- [2026-11-10] **[Verify]**
  Recorded the task outcomes.
  - Files touched: 9.
  - Lines touched: 572.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude-2: The helper removal is complete and clean.
  - Findings: [review-findings-1.md](T0044-rebuild-the-capture-view-cli-on-toolharness-and/review-findings-1.md).

- [2026-11-10] **[Decided]**
  Spec deviation: the auth capture-view.py integration check fails because auth imports removed helpers directly, not via a missing dependency; substituted a read-only shim check and backlogged auth T0217.

- [2026-11-10] **[Implement]**
  Round 1 rework: run_capture_cli now dispatches an action named after leading options, skipping option values, and inserts capture otherwise.
  - Added red-proven tests for --verbose list, --debug tour, --log-file list.
  - 1041 passed, 3 skipped.

- [2026-11-10] **[Verify]**
  Recorded the task outcomes after round 1 rework; Size note: still above the typical line, below three times the estimate.
  - Files touched: 9.
  - Lines touched: 641.
  - Reopenings: 0.

