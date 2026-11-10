---
id: T0096
owner: ~
needs: []
branch: —
worktree: —
status: cancelled
started_at: —
ended_at: "2026-11-10T15:28:36Z"
review: agent
preview: none
protocol: standard
---
# T0096: Remove publish.yml, since ReleasePipeline already attaches the wheel and sdist to the GitHub release

## Goals
Remove publish.yml, since ReleasePipeline already attaches the wheel and sdist to the GitHub release.

## Task Execution Steps
- [ ] **[Implement]** Implement required changes for T0096.
- [ ] **[Verify]**    Verify implementation with automated test suites.
- [ ] **[Doc]**       Update documentation and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Cancelled]**
  Kept publish.yml: docs/devops.md relies on it to replace local assets with a clean CI build and to cover manual releases.

