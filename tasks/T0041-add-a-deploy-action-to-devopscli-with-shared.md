---
id: T0041
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
# T0041: Add a deploy action to DevopsCli with shared preconditions, typed confirmation, project deploy steps, and post-deploy verification

## Goals
Add a `deploy` action to `DevopsCli`, enabled by `set_deploy(steps, verify=None)`, where steps are named commands or callables.
Check shared preconditions first: clean tree, non-`-pre` version, tag `v<version>` on origin, and a successful CI run for HEAD.
Require typed confirmation `deploy v<version>` unless `--yes`; `--dry-run` prints the plan and runs nothing.
Run the steps in order, stopping at the first failure, then the optional verification callback.

## Task Execution Steps
- [ ] **[Read]**      Read the production deploy flows in ../auth/scripts/devops.py and ../template.python/scripts/devops.py.
- [ ] **[Implement]** Write failing tests for preconditions, dry run, confirmation, step failures, and verification.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Implement DeployStep, DeployContext, set_deploy, and the deploy action.
- [ ] **[Verify]**    Run the full suite, including the local bare-remote integration scenario.
- [ ] **[Doc]**       Document the deploy action in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Deploy steps stay project-local; preconditions, confirmation, and verification are shared, per ADR-0003.
