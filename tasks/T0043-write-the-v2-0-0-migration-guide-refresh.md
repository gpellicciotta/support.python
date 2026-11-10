---
id: T0043
owner: "@claude"
session: claude-20261110-6243cc
needs: []
branch: task/T0043-write-the-v2-0-0-migration-guide-refresh
worktree: .plan/work/T0043-write-the-v2-0-0-migration-guide-refresh
status: active
started_at: "2026-11-10T04:44:13Z"
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
- [x] **[Read]**      Read the v2.0.0-pre CHANGELOG entries, ADR-0003, and every docs/tools page.
- [x] **[Doc]**       Write docs/migration-v2.md covering every breaking change in the v2.0.0-pre CHANGELOG section.
- [x] **[Doc]**       Refresh CLAUDE.md, and link the guide from README.md, docs/index.md, and CHANGELOG.md.
- [x] **[Implement]** Create the consumer Backlog tasks with plan tasks create --project, using the spec's wording.
- [x] **[Verify]**    Run lint-markdown check --offline on the changed documents and plan tasks validate per consumer.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Consumer migrations wait for the v2.0.0 release, which the user runs as an outbound step.

- [2026-11-10] **[Implement]**
  Created consumer Backlog tasks for all 13 repositories in the spec, each needing the released support-python v2.0.0.
  - dev-guidelines T0190, template.python T0014, template.java T0030.
  - support.java T0005, support.js T0027, auth T0218.
  - counters.server T0267, todos.server T0211, plan T0606, meteo T0029.
  - todos.webapp T0218, verkeersregels-quiz T0092, family-portal T0175.

- [2026-11-10] **[Decide]**
  Fixed existing lint findings in the declared README.md and CHANGELOG.md, because the completion check requires lint-markdown to exit 0.

- [2026-11-10] **[Verify]**
  The lint-markdown completion check exited 0. Consumer validation passed everywhere except an existing TF017 failure in todos.webapp T0047.
  - Files touched: 5.
  - Lines touched: 254.
  - Reopenings: 0.

