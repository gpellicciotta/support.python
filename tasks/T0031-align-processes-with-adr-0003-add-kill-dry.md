---
id: T0031
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
# T0031: Align processes with ADR-0003: add kill --dry-run and rename the table output format to text

## Goals
Add `--dry-run` to `processes kill`, reporting each target and whether it is protected, terminating nothing.
Rename the `--format` value `table` to `text`, keeping `json`; `--format table` exits 2.
Write `docs/tools/processes.md`.

## Task Execution Steps
- [ ] **[Read]**      Read the processes kill and list actions and their output formatting.
- [ ] **[Implement]** Write failing tests for kill --dry-run and the text and json format values.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Add kill --dry-run and rename the table format value to text.
- [ ] **[Verify]**    Run the full suite and the installed integration scenario from the technical spec.
- [ ] **[Doc]**       Write docs/tools/processes.md, and update README.md, docs/index.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Every writing action gets --dry-run and every listing uses text or json formats.
