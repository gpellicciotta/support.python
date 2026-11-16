---
id: T0113
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0113: Let devops deploy take an optional version and deploy it from a temporary worktree of its tag

## Goals
Let `deploy` take an optional version and deploy that release from a temporary worktree of its tag.
The active working tree, index, and branch stay untouched, so deploying works from `main` after a release.
Bare `deploy` keeps its current behavior.
See the companion technical specification for behavior and tests.

## Task Execution Steps
- [ ] **[Implement]** Author failing unit and integration tests from the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail for the right reason.
- [ ] **[Implement]** Add `root` to `DeployContext` and run command steps there.
- [ ] **[Implement]** Add the version argument, temporary worktree, tag checks, and guaranteed cleanup.
- [ ] **[Verify]**    Run the deploy tests and the full fast suite.
- [ ] **[Doc]**       Update devops-scripts.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-16] **[Doc]**
  Companion task file scaffolded at task creation.
