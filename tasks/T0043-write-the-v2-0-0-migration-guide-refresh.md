---
id: T0043
owner: "@claude"
session: claude-20261110-6243cc
needs: []
branch: task/T0043-write-the-v2-0-0-migration-guide-refresh
worktree: .plan/work/T0043-write-the-v2-0-0-migration-guide-refresh
status: completed
started_at: "2026-11-10T05:02:11Z"
ended_at: "2026-11-10T05:11:06Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 6, duration_s: 1512.0, input: 348, output: 93590, cache_read: 20109780, cache_write: 317946}
  review: {turns: 4, duration_s: 953.8, input: 184, output: 41332, cache_read: 6072936, cache_write: 234170}
review_status: approved
review_round: 2
work_duration: 1197.3
reviewed_by: "@claude-2"
completion-commit: 70afcd5059706d53516c56d76eed8aa5e3fa2fe2
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
- [x] **[Review]**    Obtain review approval of the finished work before completion.

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

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude-2: Most of the work is solid.
  - Findings: [review-findings-1.md](T0043-write-the-v2-0-0-migration-guide-refresh/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Reworked review round 1: reverted the frozen v1.3.0 CHANGELOG edits, bumped to 2.0.29-pre, and scoped the guide's dry-run and format claims.
  - Recorded the agent-digest option gap as Backlog task T0048.

- [2026-11-10] **[Verify]**
  Pytest passed with 1041 tests. The lint completion check fails only on six moved-file links in the frozen v1.3.0 section.

- [2026-11-10] **[Implement]**
  Touched undeclared pyproject.toml for the required version bump; recount is 6 files and 250 lines, under the typical line.

- [2026-11-10] **[Decided]**
  Orchestrator amended the completion check: frozen CHANGELOG sections stay immutable, so the six v1.3.0 moved-file links are accepted.
  - Verified: all six lint issues sit in the frozen v1.3.0 section.

- [2026-11-10] **[Verify]**
  The amended completion check passes: all six lint issues sit in frozen v1.3.0 lines 54 to 58, and consumer validation is unchanged.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude-2: Approved.
  - Findings: [review-findings-2.md](T0043-write-the-v2-0-0-migration-guide-refresh/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

