---
id: T0038
owner: "@claude"
session: claude-20261110-41556b
needs: []
branch: task/T0038-add-devopscli-and-pythonproject-to-support-python-devops
worktree: .plan/work/T0038-add-devopscli-and-pythonproject-to-support-python-devops
status: active
started_at: "2026-11-10T02:46:48Z"
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
- [x] **[Read]**      Read scripts/devops.py, ../template.python/scripts/devops.py, ToolHarness, and ReleasePipeline.
- [x] **[Implement]** Write failing tests for every DevopsCli action against a PythonProject with a stubbed runner.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement Project, PythonProject, and DevopsCli, and rebuild scripts/devops.py on them.
- [x] **[Verify]**    Run the full suite and the scripts/devops.py integration commands from the technical spec.
- [x] **[Doc]**       Update docs/devops.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Consumers keep a thin scripts/devops.py; there is no global devops command.

- [2026-11-10] **[Implement]**
  Added Project, PythonProject, and DevopsCli; rebuilt scripts/devops.py as a thin DevopsCli(PythonProject) script.
  - Undeclared file: tests/test_devops.py, expected __all__ list.
  - Test options pass after --, test paths as SELECTION.

- [2026-11-10] **[Verify]**
  Full suite and both integration commands passed; proof recorded in validation-proof.md.
  - devops.py check: 890 passed, build succeeded.
  - devops.py versions: exit 0.

- [2026-11-10] **[Decide]**
  Size note: crossed the typical line at 9 files and 744 lines; CLI, adapter, and dogfooded script form one contract.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 9.
  - Lines touched: 744.
  - Reopenings: 0.

