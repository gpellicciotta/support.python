---
id: T0042
owner: ~
needs: [T0041]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0042: Add opt-in docker, db, server, mail, and client action groups to DevopsCli, backed by the devops service managers

## Goals
Add `DevopsCli.add_services(...)`, registering opt-in action groups backed by `support_python.devops.services`.
Support group actions with a positional sub-action, such as `devops db start`.
Match the command shapes and options of ../auth/scripts/devops.py, so consumers can replace their copies.

## Task Execution Steps
- [ ] **[Read]**      Read the docker, db, server, mail, and client parsers in the auth, counters.server, and todos.server devops scripts.
- [ ] **[Implement]** Write failing tests for every group and sub-action against mocked service managers.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Implement add_services, the group actions, and sub-action dispatch.
- [ ] **[Verify]**    Run the full suite and the read-only docker status integration check.
- [ ] **[Doc]**       Document the service action groups in README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The groups replace about 2,400 near-identical lines in each of auth, counters.server, and todos.server.
