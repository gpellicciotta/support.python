---
id: T0073
owner: "@gemini"
session: antigravity-20261110-6e06c7
needs: []
branch: task/T0073-fail-the-test-run-when-a-test-writes
worktree: .plan/work/T0073-fail-the-test-run-when-a-test-writes
status: active
started_at: "2026-11-10T18:53:37Z"
ended_at: —
review: none
preview: none
protocol: adhoc
usage:
  worker: {turns: 4, duration_s: 4645.0, input: 2422516, output: 174472, cache_read: 43644788}
work_duration: 2362.6
---
# T0073: Fail the test run when a test writes into the real home directory or the repository's own .plan directory

## Goals
Add a session fixture in `tests/conftest.py` pointing `HOME`, `USERPROFILE`, `APPDATA`, and `XDG_CONFIG_HOME` at a temporary directory.
Fail the test run when any test creates, changes, or deletes files under the real home directory or the repository's `.plan/`.
Fix every test the guard catches.

## Task Execution Steps
- [x] **[Read]**      Read the testing guidelines and list tests that call `Path.home()` or `expanduser`.
- [x] **[Implement]** Write a failing test proving a deliberate write under the real home directory fails the run.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Add the redirecting fixture and the snapshot guard to conftest.py, then fix the tests it catches.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Note the guard in AGENTS.md boundaries and add a CHANGELOG.md entry.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Review lowered from agent to none by @<your name>: Very simple task..

- [2026-11-10] **[Read]**
  Read testing guidelines and cataloged tests invoking Path.home() and expanduser.

- [2026-11-10] **[Implement]**
  Authored red-phase guard tests in tests/test_conftest_guard.py.

- [2026-11-10] **[Verify]**
  Executed red-phase tests, confirmed expected collection failures, and documented in validation-proof.md.

- [2026-11-10] **[Implement]**
  Added conftest session fixture redirecting home and real-state write guard in tests/conftest.py.

- [2026-11-10] **[Verify]**
  Ran affected test suites, confirmed green-phase passing, and documented in validation-proof.md.

- [2026-11-10] **[Doc]**
  Updated AGENTS.md boundaries and added entry to CHANGELOG.md.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 4
  - Lines touched: 333
  - Reopenings: 0

