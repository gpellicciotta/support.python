---
id: T0084
owner: "@claude"
session: claude-20261111-fffa55
needs: []
branch: task/T0084-remove-the-auth-and-counters-schema-transformers-and
worktree: .plan/work/T0084-remove-the-auth-and-counters-schema-transformers-and
status: completed
started_at: "2026-11-11T00:14:19Z"
ended_at: "2026-11-11T00:22:46Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 855.4, input: 204, output: 55946, cache_read: 9335840, cache_write: 230258}
  review: {turns: 2, duration_s: 69.4, input: 24, output: 3504, cache_read: 417132, cache_write: 54514}
work_duration: 506.5
review_status: approved
review_round: 1
reviewed_by: "@claude-2"
completion-commit: 58ba25a33b605128a4be6c5a7be94e2ddd6f7e79
---
# T0084: Remove the auth and counters schema transformers and the app parameter from the SQL anonymizer, requiring a transformers map

## Goals
Remove the `auth` and `counters` schema knowledge from `support_python.sql` and the snapshot code.
Delete the six `transform_auth_*` and `transform_counters_*` functions and the `app` and `custom_password` parameters.
`anonymize_sql_stream` and `anonymize_sql_string` take a required `transformers` mapping instead.
`LocalMySqlManager` takes snapshot transformers as a constructor argument and refuses to snapshot without them.
The auth and counters repositories define their rules locally when they upgrade, tracked in their backlogs.

## Task Execution Steps
- [x] **[Read]**      Read T0083's builder, the services snapshot path, and the migration-v2.md table format.
- [x] **[Implement]** Capture golden outputs of the auth and counters sample dumps from the current code into tests/fixtures/sql/.
- [x] **[Implement]** Write failing tests for the required transformers argument, the removed names, and the snapshot refusal.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Remove the schema transformers and parameters, and add snapshot transformers to LocalMySqlManager.
- [x] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Update sql-anonymizer.md, index.md, migration-v2.md, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 2 errors; pending fix turn 1 of 2.
  - TF018.
  - TF020.

- [2026-11-11] **[Read]**
  Read the SQL builder, services snapshot path, and migration table format.

- [2026-11-11] **[Implement]**
  Captured golden outputs of auth and counters sample dumps into tests/fixtures/sql.

- [2026-11-11] **[Implement]**
  Wrote failing tests for required transformers, removed names, and snapshot refusal.

- [2026-11-11] **[Verify]**
  Recorded 25 expected red-phase failures in validation-proof.md.

- [2026-11-11] **[Implement]**
  Removed schema transformers and app parameters; added snapshot_transformers to LocalMySqlManager.

- [2026-11-11] **[Verify]**
  devops check passed with 1106 fast and 159 slow tests; evidence recorded.

- [2026-11-11] **[Doc]**
  Updated tutorial, index, requirements, migration-v2.md, and CHANGELOG.md.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 approved by @claude-2: Work meets all goals.
  - Findings: [review-findings-1.md](T0084-remove-the-auth-and-counters-schema-transformers-and/review-findings-1.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

