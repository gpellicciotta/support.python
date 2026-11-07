---
id: T0017
owner: ~
needs: [T0015]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0017: Parameterize the ported agent-files sync with configurable digest, skills, marker, and tool registry

## Goals
Replace the hard-coded repository root, digest path, skills directory, marker text, manifest source name, and `LEGACY_SKILL_NAMES` with settings from `agent-files.json` and flags.
Make the tool registry data-driven, with `claude`, `antigravity`, and `codex` as default entries.
Keep the current marker text working so installed files do not change.
Prerequisite: T0015 merged. Ends with release 1.3.0 prepared per `docs/devops.md`.

Completion check: dev-guidelines config yields an empty dry-run diff, and a second fixture project with another marker syncs correctly.
Size estimate: 5 files, 300 lines.

## Task Execution Steps
- [ ] **[Read]**      List every hard-coded dev-guidelines value in agent_files.py and how each is used.
- [ ] **[Implement]** Author failing tests for config loading, a second marker, and an added tool entry.
- [ ] **[Verify]**    Run the new tests and confirm they fail for the expected reasons.
- [ ] **[Implement]** Add the JSON config loader, flags, and the data-driven tool registry.
- [ ] **[Verify]**    Run the full suite and confirm the dev-guidelines config gives an empty dry-run diff.
- [ ] **[Doc]**       Document the config schema, update CHANGELOG.md, and prepare the 1.3.0 release.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.
