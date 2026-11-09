---
id: T0036
owner: ~
needs: [T0035]
branch: —
worktree: —
status: ready
started_at: —
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
- [ ] **[Read]**      Read the release() flow in ../template.python/scripts/devops.py and the T0035 helpers.
- [ ] **[Implement]** Write failing tests for preconditions, dry run, confirmation, freezing, and the full release flow.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Implement ReleasePipeline and confirm_typed, and export them from support_python.devops.
- [ ] **[Verify]**    Run the full suite, including the local bare-remote integration scenario.
- [ ] **[Doc]**       Document ReleasePipeline in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The pipeline follows template.python's release flow with one confirmation before any change.
