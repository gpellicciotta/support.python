---
id: T0068
owner: "@claude"
session: claude-20261111-3dfcb8
needs: []
branch: task/T0068-move-git-repository-backup-settings-onto-the-shared
worktree: .plan/work/T0068-move-git-repository-backup-settings-onto-the-shared
status: active
started_at: "2026-11-11T01:01:38Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 649.2, input: 120, output: 52292, cache_read: 5585792, cache_write: 224264}
work_duration: 337.1
---
# T0068: Move git-repository-backup settings onto the shared resolver, adding environment variables, a system file, and the config group.

## Goals
Resolve git-repository-backup settings with `SettingsSchema` and `resolve_settings` from config.py, removing the tool's own resolver.
Read options, then `GIT_REPOSITORY_BACKUP_*` variables, the user file, the system file, then defaults; the tool has no project file.
Keep the deprecated old and legacy user-file locations with their v3.0.0 warnings.
Ignore unknown keys and malformed files with one warning instead of exiting 2.
Add the `config` group through `add_config_actions`, targeting the user file by default.

## Task Execution Steps
- [x] **[Read]**      Read the configuration guidelines, config.py, and the configuration tutorial before changing the tool.
- [x] **[Implement]** Write failing tests for environment variables, system file, unknown keys, malformed files, and config actions.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Declare the settings in a `SettingsSchema` and resolve them with `resolve_settings` and `add_config_actions`.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document every setting in git-repository-backup.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read the configuration guidelines, config.py, and the configuration tutorial.

- [2026-11-11] **[Implement]**
  Wrote failing tests for environment variables, system file, unknown keys, malformed files, and config actions.

- [2026-11-11] **[Verify]**
  Ran the new tests; 16 failed, recorded as red-phase proof in validation-proof.md.

- [2026-11-11] **[Implement]**
  Declared a SettingsSchema, resolved settings with resolve_settings, and added the config group.

- [2026-11-11] **[Verify]**
  Fast suite passed with 1156 tests and slow backup tests passed with 58; output recorded.

- [2026-11-11] **[Doc]**
  Documented every setting in git-repository-backup.md and added CHANGELOG.md and migration entries.

