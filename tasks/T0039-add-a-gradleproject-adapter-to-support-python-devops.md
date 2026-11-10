---
id: T0039
owner: "@claude"
session: claude-20261110-264df3
needs: []
branch: task/T0039-add-a-gradleproject-adapter-to-support-python-devops
worktree: .plan/work/T0039-add-a-gradleproject-adapter-to-support-python-devops
status: active
started_at: "2026-11-10T03:13:34Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 1111.6, input: 164, output: 55758, cache_read: 5786078, cache_write: 161414}
work_duration: 406.1
review_status: pending
review_round: 1
---
# T0039: Add a GradleProject adapter to support_python.devops for gradlew-based lint, test, build, check, clean, and release

## Goals
Add `GradleProject` to `support_python.devops.projects`, running the Gradle wrapper (`gradlew.bat` on Windows, `./gradlew` elsewhere).
Map lint, format, test, build, check, and clean to the Gradle tasks in the technical spec, with overridable task lists.
Read and write the version in `gradle.properties`, and release built jars as assets.
Allow delegating `release` to a Gradle task instead of `ReleasePipeline`.

## Task Execution Steps
- [x] **[Read]**      Read ../template.java/scripts/devops.py, ../support.java/scripts/devops.py, and PythonProject.
- [x] **[Implement]** Write failing tests for task mapping, overrides, wrapper selection, assets, and release delegation.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement GradleProject and export it from support_python.devops.
- [x] **[Verify]**    Run the full suite and the integration checks from the technical spec.
- [x] **[Doc]**       Document GradleProject in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The Gradle mapping mirrors template.java, which support.java shares.

- [2026-11-10] **[Verify]**
  Red phase: tests/test_devops_projects_gradle.py fails at collection with ImportError, since GradleProject does not exist yet.
  - Command: python -m pytest -q tests/test_devops_projects_gradle.py, run with the main checkout's venv.

- [2026-11-10] **[Decide]**
  Added a Project.release hook that DevopsCli tries before ReleasePipeline; this touches cli.py, outside the declared files.
  - No cli.py change would let a project replace ReleasePipeline.
  - tests/test_devops.py export pin also gained GradleProject.

- [2026-11-10] **[Decide]**
  Every Gradle call adds --console=plain via gradle_options, and release_args carry template.java's -PreleaseConfirmed=yes after confirmation.
  - Dry-run release runs the task with Gradle's --dry-run and no prompt.
  - Test selection items starting with - pass through without --tests.

- [2026-11-10] **[Verify]**
  Full suite passed (924 passed, 3 skipped) apart from the export pin, fixed and rerun; ruff check and format pass.
  - Fake gradlew.bat integration test records --console=plain build for check.
  - DevopsCli(GradleProject(template.java)).run(['versions']) exited 0; template.java stayed clean.

- [2026-11-10] **[Doc]**
  Documented GradleProject's task mapping, overrides, assets, and release delegation in README.md and CHANGELOG.md.
  - lint-markdown reports no new issues on the edited lines.

- [2026-11-10] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF018.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

