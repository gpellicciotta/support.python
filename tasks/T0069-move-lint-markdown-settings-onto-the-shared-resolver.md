---
id: T0069
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
# T0069: Move lint-markdown settings onto the shared resolver, adding user and system files, environment variables, and the config group

## Goals
Resolve lint-markdown settings with `SettingsSchema` and `resolve_settings` from config.py.
Read options, then `LINT_MARKDOWN_*` variables, `.lint-markdown.json`, the user file, the system file, then defaults.
Keep the legacy `.markdown-lint.json` fallback and its v3.0.0 deprecation warning.
Replace list settings such as `enable`, `disable`, `exclude`, and `plugins` as a whole across sources.
Add the `config` group through `add_config_actions`, targeting the project file by default.

## Task Execution Steps
- [ ] **[Read]**      Read the configuration guidelines, config.py, and profiles.py before changing the tool.
- [ ] **[Implement]** Write failing tests for environment variables, user and system files, list replacement, and config actions.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Resolve the profile settings through `SettingsSchema`, keeping `load_profile` behavior for library callers.
- [ ] **[Verify]**    Run the fast suite and affected slow tests, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document every setting in lint-markdown.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
