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
usage:
  worker: {turns: 4, duration_s: 2296.0, input: 304, output: 112434, cache_read: 17342702, cache_write: 315372}
  review: {turns: 2, duration_s: 426.2, input: 56, output: 15348, cache_read: 1455358, cache_write: 104324}
review_status: pending
review_round: 2
work_duration: 865.9
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

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude-2: Most of the work is solid and matches the spec.
  - Findings: [review-findings-1.md](T0038-add-devopscli-and-pythonproject-to-support-python-devops/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Rework round 1: added a post-freeze ReleasePipeline build hook; release attaches frozen-version assets, not the -pre check build.
  - Undeclared: release.py, test_devops_release_pipeline.py.
  - Docs: Automated and Manual Release sections.

- [2026-11-10] **[Verify]**
  Full suite passed; release dry run plans build before tag; frozen build yields 2.0.22 assets.
  - pytest: 895 passed, 3 skipped.
  - Proof in validation-proof.md, Review Round 1 Rework.

- [2026-11-10] **[Decide]**
  Size note: rework raised the diff to 11 files and 883 lines, still under the large line.

- [2026-11-10] **[Verify]**
  Recorded task outcomes after review round 1 rework.
  - Files touched: 11.
  - Lines touched: 883.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

