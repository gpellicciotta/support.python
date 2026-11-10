---
id: T0057
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T11:25:29Z"
ended_at: "2026-11-10T11:33:53Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-subagent"
completion-commit: 6eb25b02ed73a128c9bd0f754a06b1f5a440cf43
---
# T0057: Use kebab-case configuration keys in all tools, still accepting snake_case keys, per the configuration guidelines

## Goals
The dev-guidelines [Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md#configuration-files) require lowercase kebab-case keys in configuration files.
Readers must accept dashes and underscores interchangeably, so existing snake_case files keep working.
support.python tools read snake_case keys today, such as `digest_path`, `skills_dir`, and `disabled_rules`.

Specifications: [technical-spec.md](T0057-use-kebab-case-configuration-keys-in-all-tools/technical-spec.md).
Completion check: `python -m pytest tests/` filtered to the configuration tests of each tool, and `ruff check src tests`
Size estimate: 10 files, 300 lines

## Task Execution Steps
- [x] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [x] **[Implement]** Normalize configuration keys once at load time, so dashes and underscores match.
- [x] **[Implement]** Switch documented, generated, and example configuration to kebab-case keys.
- [x] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [x] **[Doc]**       Update `docs/tools/*.md`, `docs/migration-v2.md`, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Verify]**
  Tests prove kebab and snake parity; full suite passed with ruff clean.
  - Files touched: 14.
  - Lines touched: 330.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-subagent.

- [2026-11-10] **[Implement]**
  Added shared normalize_config_keys; wired agent-files, lint-markdown profiles, and git-repository-backup; docs and CHANGELOG updated.

- [2026-11-10] **[Review]**
  Subagent review approved; follow-ups: unknown-key messages, tool logger passing, extra tests.

- [2026-11-10] **[Complete]**
  Task completed successfully.

