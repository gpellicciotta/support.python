---
id: T0070
owner: "@claude"
session: claude-20261111-22bb50
needs: []
branch: task/T0070-move-agent-files-settings-onto-the-shared-resolver
worktree: .plan/work/T0070-move-agent-files-settings-onto-the-shared-resolver
status: active
started_at: "2026-11-11T01:17:55Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 724.0, input: 168, output: 82778, cache_read: 8935516, cache_write: 259304}
work_duration: 350.2
review_status: pending
review_round: 1
---
# T0070: Move agent-files settings onto the shared resolver, adding user and system files, environment variables, and the config group

## Goals
Resolve agent-files settings with `SettingsSchema` and `resolve_settings` from config.py.
Read options, then `AGENT_FILES_*` variables, `.agent-files.json`, the user file, the system file, then defaults.
Merge the `tools` registry across sources by tool name, as dictionary settings merge key by key.
Ignore unknown keys and malformed files with one warning, listing unknown keys in `--debug` output.
Add the `config` group through `add_config_actions`, targeting the project file by default.

## Task Execution Steps
- [x] **[Read]**      Read the configuration guidelines, config.py, and agent_files_config.py before changing the tool.
- [x] **[Implement]** Write failing tests for environment variables, user and system files, tools merging, and config actions.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Resolve `AgentFilesConfig` through `SettingsSchema`, keeping `load_agent_files_config` working for library callers.
- [x] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document every setting in agent-files.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read the configuration guidelines, config.py, and agent_files_config.py before changing the tool.

- [2026-11-11] **[Implement]**
  Wrote failing tests for environment variables, user and system files, tools merging, and config actions.

- [2026-11-11] **[Verify]**
  Recorded 14 expected red-phase failures in validation-proof.md.

- [2026-11-11] **[Implement]**
  Resolved AgentFilesConfig through SettingsSchema, added Setting.normalize, and kept load_agent_files_config working for library callers.

- [2026-11-11] **[Verify]**
  Fast suite passed with 1186 tests and affected slow tests passed; output recorded in validation-proof.md.

- [2026-11-11] **[Doc]**
  Documented every setting in agent-files.md and added CHANGELOG.md and migration entries.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

