---
id: T0034
owner: ~
needs: [T0023]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0034: Convert support_python.devops into a package with steps and services modules, keeping its public imports unchanged

## Goals
Turn `src/support_python/devops.py` into a `support_python.devops` package: `steps.py` holds the subprocess helpers and `services.py` the service managers.
Keep every current public name importable from `support_python.devops` through `__init__.py` re-exports.
Change no behavior; update only mock patch targets in tests.

## Task Execution Steps
- [ ] **[Read]**      Read devops.py, its __all__, and every test patch target referencing support_python.devops.
- [ ] **[Implement]** Write a test importing every pre-split public name from support_python.devops and its new modules.
- [ ] **[Verify]**    Run the new test and record its failure as red-phase proof.
- [ ] **[Implement]** Run the git mv command, extract steps.py, add re-exports, and fix test patch targets.
- [ ] **[Verify]**    Run the full suite and the consumer import check from the technical spec.
- [ ] **[Doc]**       Update CLAUDE.md and CHANGELOG.md for the new module layout.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The devops package prepares room for release, projects, and cli modules.
