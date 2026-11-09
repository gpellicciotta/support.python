---
id: T0040
owner: ~
needs: [T0039]
branch: —
worktree: —
status: ready
started_at: —
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
- [ ] **[Read]**      Read ../support.js/scripts/devops.py, ../todos.webapp/scripts/devops.py, and PythonProject.
- [ ] **[Implement]** Write failing tests for script mapping, missing scripts, packing, and assets.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Implement NodeProject and export it from support_python.devops.
- [ ] **[Verify]**    Run the full suite and the integration checks from the technical spec.
- [ ] **[Doc]**       Document NodeProject in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The npm mapping mirrors support.js and todos.webapp.
