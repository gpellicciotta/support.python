---
id: T0107
owner: "@codex"
session: codex-20261112-b48c17
needs: []
branch: task/T0107-let-devops-versions-version-set-the-version-file
worktree: .plan/work/T0107-let-devops-versions-version-set-the-version-file
status: active
started_at: "2026-11-11T23:18:06Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 579.6, input: 128810, output: 15534, cache_read: 2431744, cache_write: 0}
review_status: pending
review_round: 1
---
# T0107: Let devops versions VERSION set the version file and top CHANGELOG heading for Gradle projects, like Python ones

## Goals
Let `devops versions VERSION` set the version in the project's version file and rename the top `-pre` CHANGELOG heading to match.
Cover `GradleProject` (`gradle.properties`) first, then `PythonProject` and `NodeProject` through the same project adapter API.
Keep `devops versions` without an argument as the drift check.
Refuse a malformed version, and refuse when the top heading is not a `-pre` heading.
Origin: support.java wrote this as a project-local `set-version` action in `scripts/devops.py`, with tests, as a reference.
Note: a positional named `version` collides with the harness's global `--version` flag, so use another `dest`.
Completion check: `python scripts/devops.py check`.

## Task Execution Steps
- [x] **[Implement]** Implement required changes for T0107.
- [x] **[Verify]**    Verify implementation with automated test suites.
- [x] **[Doc]**       Update documentation and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-11] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-12] **[Implement]**
  Added shared version setter, optional CLI version, strict input and heading validation, dry runs, and three-adapter regression coverage.

- [2026-11-12] **[Verify]**
  Running python scripts/devops.py check; tool session 44598; reported pytest PID 20440, ruff PIDs 66444 and 4384.

- [2026-11-12] **[Verify]**
  Full check passed: 1258 fast tests, 166 slow tests, Ruff, formatting, and builds. Markdown lint passed. Evidence: validation-proof.md. Session 91259; pytest PIDs 72392/82344; build PID 14664.

- [2026-11-12] **[Review]**
  Round 1 requested (mode: agent).

