---
id: T0043
owner: ~
needs: ['T0031', 'T0032', 'T0033', 'T0037', 'T0040', 'T0042', 'T0044']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0043: Write the v2.0.0 migration guide, refresh CLAUDE.md, and record migration backlog tasks in consumer repositories

## Goals
Write `docs/migration-v2.md`, mapping every removed or renamed command, module, option, verb, and config file to its v2.0.0 replacement.
Refresh the `CLAUDE.md` overview, Commands, and Architecture sections for the v2.0.0 layout.
Link the guide from `README.md`, `docs/index.md`, and the v2.0.0-pre `CHANGELOG.md` section.
Record one Backlog task per consumer repository in the technical spec with `plan tasks create --project`.

## Task Execution Steps
- [ ] **[Read]**      Read the v2.0.0-pre CHANGELOG entries, ADR-0003, and every docs/tools page.
- [ ] **[Doc]**       Write docs/migration-v2.md covering every breaking change in the v2.0.0-pre CHANGELOG section.
- [ ] **[Doc]**       Refresh CLAUDE.md, and link the guide from README.md, docs/index.md, and CHANGELOG.md.
- [ ] **[Implement]** Create the consumer Backlog tasks with plan tasks create --project, using the spec's wording.
- [ ] **[Verify]**    Run lint-markdown check --offline on the changed documents and plan tasks validate per consumer.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Consumer migrations wait for the v2.0.0 release, which the user runs as an outbound step.
