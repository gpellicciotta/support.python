---
id: T0093
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: cancelled
started_at: "2026-11-10T15:14:39Z"
ended_at: "2026-11-10T15:16:33Z"
review: agent
preview: none
protocol: standard
---
# T0093: Make GradleProject.release refuse a version without -pre before the confirmation, as ReleasePipeline does

## Goals
Make GradleProject.release refuse a version without -pre before the confirmation, as ReleasePipeline does.

## Task Execution Steps
- [ ] **[Implement]** Implement required changes for T0093.
- [ ] **[Verify]**    Verify implementation with automated test suites.
- [ ] **[Doc]**       Update documentation and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  ReleasePipeline accepts frozen versions to resume a release, so a hard -pre refusal in GradleProject would be inconsistent; reverted the draft.
  - Files touched: 0.
  - Lines touched: 0.
  - Reopenings: 0.

- [2026-11-10] **[Cancelled]**
  ReleasePipeline accepts frozen versions for resumed releases; release tasks such as doFullRelease own the -pre precondition.

