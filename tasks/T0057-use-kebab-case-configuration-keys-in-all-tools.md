---
id: T0057
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: active
started_at: "2026-11-10T11:25:29Z"
ended_at: —
review: agent
preview: none
protocol: standard
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
- [ ] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [ ] **[Implement]** Normalize configuration keys once at load time, so dashes and underscores match.
- [ ] **[Implement]** Switch documented, generated, and example configuration to kebab-case keys.
- [ ] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [ ] **[Doc]**       Update `docs/tools/*.md`, `docs/migration-v2.md`, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
