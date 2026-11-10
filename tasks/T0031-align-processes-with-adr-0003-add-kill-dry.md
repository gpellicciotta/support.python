---
id: T0031
owner: "@claude"
session: claude-20261110-f5c3f8
needs: []
branch: task/T0031-align-processes-with-adr-0003-add-kill-dry
worktree: .plan/work/T0031-align-processes-with-adr-0003-add-kill-dry
status: active
started_at: "2026-11-10T01:17:13Z"
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
- [x] **[Read]**      Read the processes kill and list actions and their output formatting.
- [x] **[Implement]** Write failing tests for kill --dry-run and the text and json format values.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Add kill --dry-run and rename the table format value to text.
- [x] **[Verify]**    Run the full suite and the installed integration scenario from the technical spec.
- [x] **[Doc]**       Write docs/tools/processes.md, and update README.md, docs/index.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Every writing action gets --dry-run and every listing uses text or json formats.

- [2026-11-10] **[Decided]**
  Real kill in the integration scenario uses --force; Windows taskkill without /F cannot stop windowless console processes.

- [2026-11-10] **[Decided]**
  JSON list mode routes log lines to stderr so stdout holds one JSON document, per ADR-0003.

- [2026-11-10] **[Verify]**
  Full suite, ruff, and the installed dry-run integration scenario passed; proof is in validation-proof.md.
  - 748 passed, 3 skipped.
  - Files touched: 6.
  - Lines touched: 170.
  - Reopenings: 0.

