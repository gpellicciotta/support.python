---
id: T0083
owner: "@gemini"
session: antigravity-20261111-5470b9
needs: []
branch: task/T0083-add-a-declarative-column-rule-transformer-builder-and
worktree: .plan/work/T0083-add-a-declarative-column-rule-transformer-builder-and
status: active
started_at: "2026-11-10T23:55:45Z"
ended_at: —
review: agent
preview: none
protocol: standard
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
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Implement]**
  Added SQL value helpers, RowView, and column-rules transformer builder.

- [2026-11-11] **[Verify]**
  Verified test_sql.py equivalence and full project check passed cleanly.

- [2026-11-11] **[Size]**
  Size note: Comprehensive unit tests and fixture equivalence tests exceed the typical line.

