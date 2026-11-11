---
id: T0109
owner: "@codex"
session: codex-20261112-8c0b03
needs: []
branch: task/T0109-let-a-release-skip-the-github-release-and
worktree: .plan/work/T0109-let-a-release-skip-the-github-release-and
status: active
started_at: "2026-11-11T23:31:04Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0109: Let a release skip the GitHub release and gh checks, and honor --skip-checks for project-owned releases

## Goals
Let a release skip the GitHub release and gh checks, and honor --skip-checks for project-owned releases.

## Task Execution Steps
- [x] **[Implement]** Author regression tests for release skip flags.
- [x] **[Verify]**    Confirm regression tests fail before implementation.
- [x] **[Implement]** Implement required changes for T0109.
- [x] **[Verify]**    Verify implementation with automated test suites.
- [x] **[Doc]**       Update documentation and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-11] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-12] **[Decided]**
  Added --skip-github-release and forwarded requested skip flags to project-owned releases. Gradle tasks receive skipChecks and skipGithubRelease properties.

- [2026-11-12] **[Verify]**
  Verified 118 affected tests and 17 subtests, Ruff, CLI help, Markdown lint, and task validation. Recorded evidence in validation-proof.md.
  - Files touched: 10.
  - Lines touched: 104.
  - Reopenings: 0.

