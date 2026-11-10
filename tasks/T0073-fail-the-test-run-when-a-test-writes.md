---
id: T0073
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
# T0073: Fail the test run when a test writes into the real home directory or the repository's own .plan directory

## Goals
Add a session fixture in `tests/conftest.py` pointing `HOME`, `USERPROFILE`, `APPDATA`, and `XDG_CONFIG_HOME` at a temporary directory.
Fail the test run when any test creates, changes, or deletes files under the real home directory or the repository's `.plan/`.
Fix every test the guard catches.

## Task Execution Steps
- [ ] **[Read]**      Read the testing guidelines and list tests that call `Path.home()` or `expanduser`.
- [ ] **[Implement]** Write a failing test proving a deliberate write under the real home directory fails the run.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Add the redirecting fixture and the snapshot guard to conftest.py, then fix the tests it catches.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Note the guard in AGENTS.md boundaries and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
