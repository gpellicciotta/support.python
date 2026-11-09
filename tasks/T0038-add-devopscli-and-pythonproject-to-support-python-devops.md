---
id: T0038
owner: ~
needs: [T0036, T0028]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0038: Add DevopsCli and PythonProject to support_python.devops, and rebuild this repository's scripts/devops.py on them

## Goals
Add `support_python.devops.projects` with a `Project` base class and `PythonProject`, and `support_python.devops.cli` with `DevopsCli` built on `ToolHarness`.
Provide the standard actions lint, format, test, build, check, clean, versions, and release, plus help and version.
Wire `release` to `ReleasePipeline`, using `check` as its quality check and the build outputs as assets.
Rebuild this repository's `scripts/devops.py` on `DevopsCli(PythonProject(...))`, keeping `bootstrap-dev-environment.py` stdlib-only.

## Task Execution Steps
- [ ] **[Read]**      Read scripts/devops.py, ../template.python/scripts/devops.py, ToolHarness, and ReleasePipeline.
- [ ] **[Implement]** Write failing tests for every DevopsCli action against a PythonProject with a stubbed runner.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Implement Project, PythonProject, and DevopsCli, and rebuild scripts/devops.py on them.
- [ ] **[Verify]**    Run the full suite and the scripts/devops.py integration commands from the technical spec.
- [ ] **[Doc]**       Update docs/devops.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Consumers keep a thin scripts/devops.py; there is no global devops command.
