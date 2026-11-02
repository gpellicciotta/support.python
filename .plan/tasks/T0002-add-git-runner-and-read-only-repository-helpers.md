---
id: T0002
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
# T0002: Add git runner and read-only repository helpers

## Goals
Add a git runner and read-only repository helpers to support_python, extracted from the plan project's `utils/git.py`. Scope: run_git_command, repo root, HEAD commit, current branch, branch existence, clean check, remote check, worktree and status porcelain parsing. Out of scope: stash, task-branch, turn-snapshot, checkpoint, merge, push, and worktree-mutation helpers, which are plan-specific.

## Task Execution Steps
- [ ] **[Read]**      Read the plan project's utils/git.py helpers named in the goals, and DEFAULT_GIT_ENV.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement git.py and re-export its public symbols from the package root.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
