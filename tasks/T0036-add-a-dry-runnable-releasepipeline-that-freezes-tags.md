---
id: T0036
owner: "@claude"
session: claude-20261110-5056ac
needs: []
branch: task/T0036-add-a-dry-runnable-releasepipeline-that-freezes-tags
worktree: .plan/work/T0036-add-a-dry-runnable-releasepipeline-that-freezes-tags
status: active
started_at: "2026-11-10T02:14:46Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0036: Add a dry-runnable ReleasePipeline that freezes, tags, pushes, publishes a GitHub release with assets, and reopens development

## Goals
Add `ReleasePipeline` to `support_python.devops.release`: preconditions, quality check, freeze, tag, push, GitHub release with assets, and reopening development.
Support `dry_run`, which prints every command and file edit without writing or running anything.
Require one typed confirmation before any change unless `assume_yes` is set, through a reusable `confirm_typed` helper.
Run commands through an injectable runner defaulting to `run_step_command`.

## Task Execution Steps
- [x] **[Read]**      Read the release() flow in ../template.python/scripts/devops.py and the T0035 helpers.
- [x] **[Implement]** Write failing tests for preconditions, dry run, confirmation, freezing, and the full release flow.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement ReleasePipeline and confirm_typed, and export them from support_python.devops.
- [x] **[Verify]**    Run the full suite, including the local bare-remote integration scenario.
- [x] **[Doc]**       Document ReleasePipeline in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The pipeline follows template.python's release flow with one confirmation before any change.

- [2026-11-10] **[Decided]**
  Added a query callable for read-only commands beside runner, and a local-tag precondition; dry runs still run read-only precondition queries.

- [2026-11-10] **[Implement]**
  Touched undeclared tests/test_devops.py to pin the three new devops exports.
  - Size note: 6 files, 680 lines; above the typical line.
  - One transaction; a partial pipeline could not release anything.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 6.
  - Lines touched: 680.
  - Reopenings: 0.

