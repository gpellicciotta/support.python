---
id: T0035
owner: ~
needs: [T0034]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0035: Add support_python.devops.release helpers for version files, CHANGELOG freezing and reopening, release notes, and GitHub origins

## Goals
Add `support_python.devops.release` with stdlib-only helpers for version files, CHANGELOG headings, release notes, and GitHub origins.
Consolidate the duplicated logic named in the technical spec, matching the existing behavior.
Leave the scripts unchanged; T0037 rebuilds them on this module.

## Task Execution Steps
- [ ] **[Read]**      Read every source implementation listed in the technical spec.
- [ ] **[Implement]** Write failing unit tests for every helper in the technical spec's API.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Implement the release helpers and export them from support_python.devops.
- [ ] **[Verify]**    Run the full suite and the integration checks against this repository from the technical spec.
- [ ] **[Doc]**       Document the release helpers in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Release logic duplicated across scripts and templates moves into one library module.
