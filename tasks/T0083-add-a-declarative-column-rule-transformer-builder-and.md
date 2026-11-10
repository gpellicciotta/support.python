---
id: T0083
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
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
- [ ] **[Read]**      Read sql.py, test_sql.py, and sql-anonymizer.md to confirm current transformer behavior and fallback positions.
- [ ] **[Implement]** Write failing unit tests for the value helpers, `column_index`, `RowView`, and `column_rules_transformer`.
- [ ] **[Implement]** Write a failing equivalence test rebuilding the auth and counters rules with the builder.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Implement the helpers and builder in sql.py and re-export them from the package root.
- [ ] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document the builder with auth and counters examples in sql-anonymizer.md, and update CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
