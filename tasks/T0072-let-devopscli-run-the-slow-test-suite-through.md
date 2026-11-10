---
id: T0072
owner: "@gemini"
session: antigravity-20261111-912b0b
needs: []
branch: task/T0072-let-devopscli-run-the-slow-test-suite-through
worktree: .plan/work/T0072-let-devopscli-run-the-slow-test-suite-through
status: active
started_at: "2026-11-10T23:39:10Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 1403.8, input: 1335996, output: 137160, cache_read: 40275918}
work_duration: 716.1
---
# T0072: Let DevopsCli run the slow test suite through test --slow, and run both suites in check and release

## Goals
Add a `--slow` option to `DevopsCli test` that runs the project's slow suite.
Make `check` and the `release` quality gate run the fast suite, then the slow suite.
Implement the slow-suite command in `PythonProject` (`pytest -m slow --timeout=120`), `GradleProject`, and `NodeProject`.
Let adapters without a slow suite skip it with an `INFO` message instead of failing.

## Task Execution Steps
- [x] **[Read]**      Read the testing guidelines and the `Project` adapters in projects.py.
- [x] **[Implement]** Write failing tests for `test --slow`, and for `check` running both suites in order.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Add a slow-test hook to `Project` and its adapters, and wire it into `test`, `check`, and `release`.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document `test --slow` in devops-scripts.md and devops.md, and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Read]**
  Read testing guidelines and adapter implementations in projects.py.
  - Read Project, PythonProject, GradleProject, NodeProject.
  - Reviewed test runner and check contracts.

- [2026-11-11] **[Implement]**
  Added automated test cases reproducing missing test --slow support.
  - Added unit tests for PythonProject slow suite.
  - Added tests for GradleProject and NodeProject.

- [2026-11-11] **[Verify]**
  Recorded red-phase test failures across all test suites.
  - 16 test cases failed as expected.
  - Captured failure output in validation-proof.md.

- [2026-11-11] **[Implement]**
  Added test_slow hook to Project adapters and wired --slow into DevopsCli.
  - PythonProject runs pytest with slow marker.
  - GradleProject and NodeProject support slow suites.

- [2026-11-11] **[Verify]**
  Verified fast suite, slow suite, and integration scenarios.
  - 112 unit tests passed.
  - 159 slow tests passed in 53.5s.

- [2026-11-11] **[Doc]**
  Documented test --slow in devops.md, devops-scripts.md, and CHANGELOG.md.
  - Documented CLI options and adapter behaviors.
  - Added CHANGELOG entry under v2.0.19-pre.

