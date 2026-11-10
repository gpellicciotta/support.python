---
id: T0041
owner: "@claude"
session: claude-20261110-6d0657
needs: []
branch: task/T0041-add-a-deploy-action-to-devopscli-with-shared
worktree: .plan/work/T0041-add-a-deploy-action-to-devopscli-with-shared
status: active
started_at: "2026-11-10T03:38:38Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 1358.2, input: 156, output: 60082, cache_read: 6812040, cache_write: 204554}
review_status: pending
review_round: 1
---
# T0041: Add a deploy action to DevopsCli with shared preconditions, typed confirmation, project deploy steps, and post-deploy verification

## Goals
Add a `deploy` action to `DevopsCli`, enabled by `set_deploy(steps, verify=None)`, where steps are named commands or callables.
Check shared preconditions first: clean tree, non-`-pre` version, tag `v<version>` on origin, and a successful CI run for HEAD.
Require typed confirmation `deploy v<version>` unless `--yes`; `--dry-run` prints the plan and runs nothing.
Run the steps in order, stopping at the first failure, then the optional verification callback.

## Task Execution Steps
- [x] **[Read]**      Read the production deploy flows in ../auth/scripts/devops.py and ../template.python/scripts/devops.py.
- [x] **[Implement]** Write failing tests for preconditions, dry run, confirmation, step failures, and verification.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Implement DeployStep, DeployContext, set_deploy, and the deploy action.
- [x] **[Verify]**    Run the full suite, including the local bare-remote integration scenario.
- [x] **[Doc]**       Document the deploy action in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Deploy steps stay project-local; preconditions, confirmation, and verification are shared, per ADR-0003.

- [2026-11-10] **[Decide]**
  Added keyword-only query and input_fn to set_deploy for injection; the origin tag must also point at HEAD.

- [2026-11-10] **[Implement]**
  Implemented DeployStep, DeployContext, DeployPipeline, and DevopsCli.set_deploy; updated the undeclared tests/test_devops.py export pin.

- [2026-11-10] **[Verify]**
  Full suite, ruff, and the bare-remote integration scenario passed; proof is in validation-proof.md.
  - 975 passed, 3 skipped.
  - 28 deploy tests passed.

- [2026-11-10] **[Doc]**
  Size note: the diff reached 7 files and 652 lines, above the typical line; 335 lines are tests, so splitting adds no value.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 7.
  - Lines touched: 652.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

