---
id: T0028
owner: ~
needs: [T0026, T0027]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0028: Make ToolHarness configure UTF-8 output for every tool, and remove the ToolLogger and TeeLogger logger aliases.

## Goals
Make `ToolHarness.run` call `configure_utf8_output()` before parsing, and delete the per-tool UTF-8 reconfiguration blocks.
Remove the `ToolLogger` and `TeeLogger` aliases from `support_python.logging` and the package root.
Replace every remaining alias use with `CliLogger` through the mechanical command in the technical spec.

## Task Execution Steps
- [ ] **[Read]**      Read ToolHarness.run, configure_utf8_output, every stream reconfiguration block, and every alias use.
- [ ] **[Implement]** Write failing tests for harness UTF-8 setup and the absence of both logger aliases.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Run the alias sweep, delete the aliases, and move UTF-8 setup into ToolHarness.run.
- [ ] **[Verify]**    Run ruff, the full suite, and each installed console script's help action.
- [ ] **[Doc]**       Update README.md and CHANGELOG.md, listing the removed aliases as breaking changes.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. UTF-8 setup belongs in ToolHarness; the logger aliases go in the breaking release.
