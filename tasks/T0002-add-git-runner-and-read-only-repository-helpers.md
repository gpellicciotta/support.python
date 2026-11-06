---
id: T0002
owner: "@codex"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-06T14:07:56Z"
ended_at: "2026-11-06T16:31:52Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 2
reviewed_by: "@codex-review"
completion-commit: a355023fdbb800fb7a8b179131d92286d6dde4a8
---
# T0002: Add git runner and read-only repository helpers

## Goals
Add a git runner and read-only repository helpers to support_python, extracted from the plan project's `utils/git.py`. Scope: run_git_command, repo root, HEAD commit, current branch, branch existence, clean check, remote check, worktree and status porcelain parsing. Out of scope: stash, task-branch, turn-snapshot, checkpoint, merge, push, and worktree-mutation helpers, which are plan-specific.

## Task Execution Steps
- [x] **[Read]**      Read the plan project's utils/git.py helpers named in the goals, and DEFAULT_GIT_ENV.
- [x] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [x] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [x] **[Implement]** Implement git.py and re-export its public symbols from the package root.
- [x] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [x] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Read]**
  Inspected source and test specifications. Awaiting clarification: preserve False on clean-check and remote-query failures, or standardize query failures as None.

- [2026-11-06] **[Decided]**
  Standardized all query failures as None at user request. Added pyproject.toml for version parity. Fixed arrow parsing for untracked filenames.

- [2026-11-06] **[Verify]**
  Full suite command python -m pytest -q runs under execution session 36639. Size note: source docstrings and failure coverage exceed 400 lines within one Git subsystem.

- [2026-11-06] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-06] **[Review]**
  Round 1 rejected by @codex-review: Preserve newlines in NUL-delimited worktree paths and restore documentation encoding.

- [2026-11-06] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-06] **[Review]**
  Round 2 approved by @codex-review.

- [2026-11-06] **[Verify]**
  Verified implementation and agent review; Markdown findings match the baseline.
  - Files touched: 8.
  - Lines touched: 589.
  - Reopenings: 0.

- [2026-11-06] **[Complete]**
  Task completed successfully.

