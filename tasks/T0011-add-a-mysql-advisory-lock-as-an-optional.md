---
id: T0011
owner: ~
needs: [T0006]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0011: Add a MySQL advisory lock as an optional extra

## Goals
Add MySQLLock to support_python, extracted from the plan project's `utils/locking.py`. It uses the server-side advisory locks GET_LOCK and RELEASE_LOCK, handling the 1, 0, and NULL results. The pymysql package is an optional extra imported lazily; the core library stays dependency-free. Extend the T0006 factory with mysql://, mysql+pymysql://, and jdbc:mysql:// URLs.

## Task Execution Steps
- [ ] **[Read]**      Read plan's MySQLLock, its URL parsing, and the pymysql extra declaration in plan's pyproject.toml.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement MySQLLock, the optional mysql extra in pyproject.toml, and the factory schemes.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
