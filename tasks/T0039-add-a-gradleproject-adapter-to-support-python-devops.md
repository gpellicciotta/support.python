---
id: T0039
owner: ~
needs: [T0038]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0039: Add a GradleProject adapter to support_python.devops for gradlew-based lint, test, build, check, clean, and release

## Goals
Add `GradleProject` to `support_python.devops.projects`, running the Gradle wrapper (`gradlew.bat` on Windows, `./gradlew` elsewhere).
Map lint, format, test, build, check, and clean to the Gradle tasks in the technical spec, with overridable task lists.
Read and write the version in `gradle.properties`, and release built jars as assets.
Allow delegating `release` to a Gradle task instead of `ReleasePipeline`.

## Task Execution Steps
- [ ] **[Read]**      Read ../template.java/scripts/devops.py, ../support.java/scripts/devops.py, and PythonProject.
- [ ] **[Implement]** Write failing tests for task mapping, overrides, wrapper selection, assets, and release delegation.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Implement GradleProject and export it from support_python.devops.
- [ ] **[Verify]**    Run the full suite and the integration checks from the technical spec.
- [ ] **[Doc]**       Document GradleProject in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The Gradle mapping mirrors template.java, which support.java shares.
