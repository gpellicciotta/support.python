---
id: T0083
owner: "@claude"
session: claude-20261111-0b6ccd
needs: []
branch: task/T0083-add-a-declarative-column-rule-transformer-builder-and
worktree: .plan/work/T0083-add-a-declarative-column-rule-transformer-builder-and
status: completed
started_at: "2026-11-10T23:55:45Z"
ended_at: "2026-11-11T00:13:59Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 1811.4, input: 1441248, output: 166470, cache_read: 46685764, cache_write: 67968}
  review: {turns: 2, duration_s: 286.0, input: 28, output: 5366, cache_read: 507472, cache_write: 55988}
work_duration: 1093.8
contributors: "@gemini"
review_status: approved
review_round: 1
reviewed_by: "@claude-2"
completion-commit: 3f7c17a160296b7b2b6f46ea0d14fb90e99201a5
---
# T0083: Add a declarative column-rule transformer builder and public SQL value helpers to the SQL anonymizer

## Goals
`support_python.sql` hardcodes the `auth` and `counters` schemas, so other projects cannot reuse its anonymizer cleanly.
Add a declarative builder that turns per-column rules into a `TableTransformer`, plus public SQL value helpers.
Any project can then describe its own tables without copying parsing or quoting code.
The auth and counters rule sets, rebuilt with the builder in tests, must reproduce today's output byte for byte.
This task only adds API; T0084 removes the hardcoded schemas.

## Task Execution Steps
- [x] **[Read]**      Read sql.py, test_sql.py, and sql-anonymizer.md to confirm current transformer behavior and fallback positions.
- [x] **[Implement]** Write failing unit tests for the value helpers, `column_index`, `RowView`, and `column_rules_transformer`.
- [x] **[Implement]** Write a failing equivalence test rebuilding the auth and counters rules with the builder.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Implement the helpers and builder in sql.py and re-export them from the package root.
- [x] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the builder with auth and counters examples in sql-anonymizer.md, and update CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Implement]**
  Added SQL value helpers, RowView, and column-rules transformer builder.

- [2026-11-11] **[Verify]**
  Verified test_sql.py equivalence and full project check passed cleanly.

- [2026-11-11] **[Size]**
  Size note: Comprehensive unit tests and fixture equivalence tests exceed the typical line.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read sql.py, test_sql.py, and sql-anonymizer.md to confirm transformer behavior.

- [2026-11-11] **[Implement]**
  Wrote unit and equivalence tests for helpers, RowView, and the builder.

- [2026-11-11] **[Doc]**
  Documented the builder in sql-anonymizer.md and updated CHANGELOG.md.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-11] **[Review]**
  Round 1 approved by @claude-2: Approved.
  - Findings: [review-findings-1.md](T0083-add-a-declarative-column-rule-transformer-builder-and/review-findings-1.md).

- [2026-11-11] **[Complete]**
  Task completed successfully.

