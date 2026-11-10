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

