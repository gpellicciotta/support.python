---
id: T0011
owner: "@gemini"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-07T09:47:32Z"
ended_at: "2026-11-07T09:55:15Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-code"
completion-commit: 7e7444044c65e262a3cda2a5836a0c6813651061
---
# T0011: Add a MySQL advisory lock as an optional extra

## Goals
Add MySQLLock to support_python, extracted from the plan project's `utils/locking.py`. It uses the server-side advisory locks GET_LOCK and RELEASE_LOCK, handling the 1, 0, and NULL results. The pymysql package is an optional extra imported lazily; the core library stays dependency-free. Extend the T0006 factory with mysql://, mysql+pymysql://, and jdbc:mysql:// URLs.

## Task Execution Steps
- [x] **[Read]**      Read plan's MySQLLock, its URL parsing, and the pymysql extra declaration in plan's pyproject.toml.
- [x] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [x] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [x] **[Implement]** Implement MySQLLock, the optional mysql extra in pyproject.toml, and the factory schemes.
- [x] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [x] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-07] **[Read]**
  Read plan's MySQLLock implementation, URL parsing schemes, and PyMySQL extra declaration.

- [2026-11-07] **[Implement]**
  Authored unit and integration tests in tests/test_locking_mysql.py.

- [2026-11-07] **[Verify]**
  Ran tests/test_locking_mysql.py and confirmed collection failure before implementation.

- [2026-11-07] **[Implement]**
  Implemented MySQLLock with URL parsing and optional mysql extra in pyproject.toml.

- [2026-11-07] **[Verify]**
  Verified tests in test_locking_mysql.py pass and ruff check and format are clean.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md, README.md, CLAUDE.md, and docs/index.md with MySQLLock documentation.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 approved by @claude-code.

- [2026-11-07] **[Complete]**
  Task completed successfully.

