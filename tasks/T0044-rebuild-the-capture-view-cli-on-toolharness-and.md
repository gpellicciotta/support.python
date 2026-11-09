---
id: T0044
owner: ~
needs: [T0028]
branch: —
worktree: —
status: ready
started_at: —
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
- [ ] **[Read]**      Read run_capture_cli, its parser, its tests, and ../auth/scripts/capture-view.py.
- [ ] **[Implement]** Write failing tests for the harness-based capture CLI and the removed argparse helpers.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Rebuild the capture CLI on ToolHarness and delete the four helpers and their exports.
- [ ] **[Verify]**    Run the full suite and the capture CLI integration check from the technical spec.
- [ ] **[Doc]**       Update README.md and CHANGELOG.md, listing the removed helpers as breaking changes.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. ToolHarness becomes the only CLI API; capture was the last user of the parallel helpers.
