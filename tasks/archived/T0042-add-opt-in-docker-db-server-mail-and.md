---
id: T0042
owner: "@claude"
session: claude-20261110-0f41f1
needs: []
branch: task/T0042-add-opt-in-docker-db-server-mail-and
worktree: .plan/work/T0042-add-opt-in-docker-db-server-mail-and
status: completed
started_at: "2026-11-10T03:54:40Z"
ended_at: "2026-11-10T04:22:03Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 2272.6, input: 108, output: 56300, cache_read: 9335826, cache_write: 88230}
  review: {turns: 4, duration_s: 912.8, input: 24, output: 8182, cache_read: 985128, cache_write: 12762}
review_status: approved
review_round: 2
work_duration: 1642.8
reviewed_by: "@claude-2"
completion-commit: 62c26fde71b59c3295621047fd62ec36117952df
---
# T0042: Add opt-in docker, db, server, mail, and client action groups to DevopsCli, backed by the devops service managers

## Goals
Add `DevopsCli.add_services(...)`, registering opt-in action groups backed by `support_python.devops.services`.
Support group actions with a positional sub-action, such as `devops db start`.
Match the command shapes and options of ../auth/scripts/devops.py, so consumers can replace their copies.

## Task Execution Steps
- [x] **[Read]**      Read the docker, db, server, mail, and client parsers in the auth, counters.server, and todos.server devops scripts.
- [x] **[Implement]** Write failing tests for every group and sub-action against mocked service managers.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement add_services, the group actions, and sub-action dispatch.
- [x] **[Verify]**    Run the full suite and the read-only docker status integration check.
- [x] **[Doc]**       Document the service action groups in README.md and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The groups replace about 2,400 near-identical lines in each of auth, counters.server, and todos.server.

- [2026-11-10] **[Decide]**
  Followed auth option names over the spec shorthand; added counters/todos aliases, a service_url default, and LocalVerifier.run_all_checks.
  - load-snapshot: positional path or --snapshot-path.
  - mail: positional recipient or --to.
  - server start: --build or --force-build.
  - status sub-actions exit 0, as in the references.

- [2026-11-10] **[Verify]**
  Red phase: 48 of 48 new tests failed before implementation.
  - 44: Mock has no attribute run_all_checks.
  - 1: DevopsCli has no attribute add_services.
  - 3: LocalVerifier has no attribute run_all_checks.

- [2026-11-10] **[Implement]**
  Added ServiceActions, DevopsCli.add_services, sub-action dispatch, and LocalVerifier.run_all_checks; 48 new tests pass.
  - Undeclared: src/support_python/devops/services.py (run_all_checks).
  - Undeclared: tests/test_devops.py (exports list).

- [2026-11-10] **[Decide]**
  Size note: diff is 8 files and 894 lines, above the typical line; one shared dispatch mechanism backs all groups.
  - Estimate 650 lines; below the large line.

- [2026-11-10] **[Verify]**
  Docker status integration check exited 0 with 'Docker Engine: NOT-INSTALLED', starting nothing.

- [2026-11-10] **[Verify]**
  Full suite passed: 1023 passed, 3 skipped; ruff check and format clean.

- [2026-11-10] **[Doc]**
  Documented the service action groups in README.md and CHANGELOG.md.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 8.
  - Lines touched: 894.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude-2: The dispatch design is clean and well tested against mocks.
  - Findings: [review-findings-1.md](T0042-add-opt-in-docker-db-server-mail-and/review-findings-1.md).

- [2026-11-10] **[Decide]**
  Rework: load_snapshot accepts testdb or any <name>_test alias, loading into that database; add_services rejects other db_targets with ValueError.
  - Safety check against the env JDBC URL is unchanged.

- [2026-11-10] **[Decide]**
  Implemented client verify-deployment --timeout via a new verify_deployment timeout parameter, and opt-in server start --testdb via testdb_env_file.
  - --testdb env-file names differ per consumer, so callers pass it.

- [2026-11-10] **[Implement]**
  Sub-actions now reject another sub-action's positional argument with exit 2, such as db snapshot stray.sql.

- [2026-11-10] **[Verify]**
  Rework red phase: 14 failures; green: full suite 1033 passed, 3 skipped; real-manager todos_test load reaches the proxy check.

- [2026-11-10] **[Decide]**
  Size note: review rework raised the diff to 1061 lines, above the large line but below three times the estimate.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 8.
  - Lines touched: 1061.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude-2: The rework resolves every round-1 defect and process gap; the task goals are met.
  - Findings: [review-findings-2.md](T0042-add-opt-in-docker-db-server-mail-and/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

