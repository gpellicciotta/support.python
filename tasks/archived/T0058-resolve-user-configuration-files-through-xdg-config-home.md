---
id: T0058
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T10:38:49Z"
ended_at: "2026-11-10T10:48:07Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-code-subagent"
completion-commit: ff582236907ff388ca6a6a4d8fed0283525d3d1b
---
# T0058: Resolve user configuration files through XDG_CONFIG_HOME or APPDATA in a shared helper, per the configuration guidelines

## Goals
Add `user_config_dir` and `user_config_path` helpers resolving the user configuration file location per the configuration guidelines.
They honor an absolute `XDG_CONFIG_HOME` everywhere, then `%APPDATA%` on Windows, then `~/.config` elsewhere.
Adopting them in `git-repository-backup` is T0059.

Specifications: [technical-spec.md](T0058-resolve-user-configuration-files-through-xdg-config-home/technical-spec.md).

## Task Execution Steps
- [x] **[Implement]** Write failing helper tests in tests/test_env.py from the technical spec.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Add user_config_dir and user_config_path to env.py and export them.
- [x] **[Verify]**    Run the full suite, ruff, and the subprocess integration scenario.
- [x] **[Doc]**       Update the script utilities tutorial, requirements.md, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  Split git-repository-backup adoption into T0059 under the one-interface sizing gate; T0058 adds only the helpers.

- [2026-11-10] **[Verify]**
  Red phase failed on the missing helpers; full suite, ruff, Python 3.9, and subprocess scenario pass.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-subagent.

- [2026-11-10] **[Review]**
  Agent reviewer approved; test-first rejected ':' in tool names and relative APPDATA, added tilde case, documented host-native paths.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 6.
  - Lines touched: 168.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

