---
id: T0084
owner: ~
needs: [T0083]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0084: Remove the auth and counters schema transformers and the app parameter from the SQL anonymizer, requiring a transformers map

## Goals
Remove the `auth` and `counters` schema knowledge from `support_python.sql` and the snapshot code.
Delete the six `transform_auth_*` and `transform_counters_*` functions and the `app` and `custom_password` parameters.
`anonymize_sql_stream` and `anonymize_sql_string` take a required `transformers` mapping instead.
`LocalMySqlManager` takes snapshot transformers as a constructor argument and refuses to snapshot without them.
The auth and counters repositories define their rules locally when they upgrade, tracked in their backlogs.

## Task Execution Steps
- [ ] **[Read]**      Read T0083's builder, the services snapshot path, and the migration-v2.md table format.
- [ ] **[Implement]** Capture golden outputs of the auth and counters sample dumps from the current code into tests/fixtures/sql/.
- [ ] **[Implement]** Write failing tests for the required transformers argument, the removed names, and the snapshot refusal.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Remove the schema transformers and parameters, and add snapshot transformers to LocalMySqlManager.
- [ ] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Update sql-anonymizer.md, index.md, migration-v2.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
