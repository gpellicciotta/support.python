---
id: T0059
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T11:02:29Z"
ended_at: "2026-11-10T11:18:45Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-code-subagent"
completion-commit: 4fd9e11ef5c533c34d17b0ac22995b3a602f50b9
---
# T0059: Make git-repository-backup find its user config through user_config_path, reading the old ~/.config location with a deprecation warning

## Goals
Make `git-repository-backup` discover its user config through `user_config_path` from T0058, per the configuration guidelines.
Keep reading the old `~/.config/git-repository-backup/config.json` with a deprecation warning when the new location differs.
On Windows the default moves to `%APPDATA%/git-repository-backup/config.json`.

Specifications: [technical-spec.md](T0059-make-git-repository-backup-find-its-user-config/technical-spec.md).

## Task Execution Steps
- [x] **[Implement]** Write failing discovery tests in tests/tools/test_git_repository_backup.py from the technical spec.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Switch default_config_path, load_config, and describe_config to the new discovery order.
- [x] **[Verify]**    Run the full suite, ruff, and the installed integration check.
- [x] **[Doc]**       Update the help text, docs/tools/git-repository-backup.md, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Verify]**
  Red phase failed six tests; full suite, ruff, and installed XDG and old-location scenarios pass.
  - Test base class now isolates XDG_CONFIG_HOME and home from the real profile.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-subagent.

- [2026-11-10] **[Review]**
  Agent reviewer approved; fixed the migration-v2 table row, split the old-only case, renamed one test, added a setUp comment.
  - Undeclared: docs/migration-v2.md.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 5.
  - Lines touched: 234.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

