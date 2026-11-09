---
id: T0029
owner: ~
needs: [T0028]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0029: Align agent-files with ADR-0003: canonical sync and check verbs, JSON list output, and .agent-files.json with legacy fallback

## Goals
Make `list`, `sync`, `check`, and `review` the canonical agent-files actions, removing the `update` and `diff` names and alias mapping.
Make `check` read-only, exiting 1 when any tool has pending changes.
Add `--format text|json` to `list` and `check`.
Read project config from `.agent-files.json`, falling back to `agent-files.json` with a warning.
Fix the stale help examples.

## Task Execution Steps
- [ ] **[Read]**      Read the agent-files action registration, alias mapping, list and diff output, and config lookup.
- [ ] **[Implement]** Write failing tests for verbs, check exit codes, JSON output, config names, and help examples.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Rename the actions, add --format, and add the config fallback in tools/agent_files_config.py.
- [ ] **[Verify]**    Run the full suite and the installed integration commands from the technical spec.
- [ ] **[Doc]**       Update docs/tools/agent-files.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. It absorbs cancelled T0022's verb and naming goals.
