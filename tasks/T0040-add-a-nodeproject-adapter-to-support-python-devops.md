---
id: T0040
owner: "@claude"
session: claude-20261110-8d03fa
needs: []
branch: task/T0040-add-a-nodeproject-adapter-to-support-python-devops
worktree: .plan/work/T0040-add-a-nodeproject-adapter-to-support-python-devops
status: active
started_at: "2026-11-10T03:27:06Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0040: Add a NodeProject adapter to support_python.devops for npm-based lint, format, test, build, check, clean, and release

## Goals
Add `NodeProject` to `support_python.devops.projects`, running npm scripts through `resolve_executable`, so Windows finds `npm.cmd`.
Map lint, format, test, build, check, and clean per the technical spec.
Read and write the version in `package.json`, and release packed tarballs as assets.

## Task Execution Steps
- [x] **[Read]**      Read ../support.js/scripts/devops.py, ../todos.webapp/scripts/devops.py, and PythonProject.
- [x] **[Implement]** Write failing tests for script mapping, missing scripts, packing, and assets.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement NodeProject and export it from support_python.devops.
- [x] **[Verify]**    Run the full suite and the integration checks from the technical spec.
- [x] **[Doc]**       Document NodeProject in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The npm mapping mirrors support.js and todos.webapp.

- [2026-11-10] **[Implement]**
  Added NodeProject; build clears dist before the build script, so outputs written to dist survive packing.

- [2026-11-10] **[Implement]**
  Touched undeclared tests/test_devops.py to add NodeProject to the pinned devops __all__; recount stays under the typical line.

- [2026-11-10] **[Verify]**
  Full suite, ruff, and both integration checks passed; output is in validation-proof.md.
  - 947 passed, 3 skipped.
  - npm check left dist/demo-2.0.1-pre.tgz.
  - support.js versions exited 0.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 6.
  - Lines touched: 334.
  - Reopenings: 0.

