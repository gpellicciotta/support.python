---
id: T0068
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
# T0068: Move git-repository-backup settings onto the shared resolver, adding environment variables, a system file, and the config group.

## Goals
Resolve git-repository-backup settings with `SettingsSchema` and `resolve_settings` from config.py, removing the tool's own resolver.
Read options, then `GIT_REPOSITORY_BACKUP_*` variables, the user file, the system file, then defaults; the tool has no project file.
Keep the deprecated old and legacy user-file locations with their v3.0.0 warnings.
Ignore unknown keys and malformed files with one warning instead of exiting 2.
Add the `config` group through `add_config_actions`, targeting the user file by default.

## Task Execution Steps
- [ ] **[Read]**      Read the configuration guidelines, config.py, and the configuration tutorial before changing the tool.
- [ ] **[Implement]** Write failing tests for environment variables, system file, unknown keys, malformed files, and config actions.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Declare the settings in a `SettingsSchema` and resolve them with `resolve_settings` and `add_config_actions`.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document every setting in git-repository-backup.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
