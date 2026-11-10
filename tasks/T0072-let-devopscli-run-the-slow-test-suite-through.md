---
id: T0072
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
# T0072: Let DevopsCli run the slow test suite through test --slow, and run both suites in check and release

## Goals
Add a `--slow` option to `DevopsCli test` that runs the project's slow suite.
Make `check` and the `release` quality gate run the fast suite, then the slow suite.
Implement the slow-suite command in `PythonProject` (`pytest -m slow --timeout=120`), `GradleProject`, and `NodeProject`.
Let adapters without a slow suite skip it with an `INFO` message instead of failing.

## Task Execution Steps
- [ ] **[Read]**      Read the testing guidelines and the `Project` adapters in projects.py.
- [ ] **[Implement]** Write failing tests for `test --slow`, and for `check` running both suites in order.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Add a slow-test hook to `Project` and its adapters, and wire it into `test`, `check`, and `release`.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document `test --slow` in devops-scripts.md and devops.md, and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
