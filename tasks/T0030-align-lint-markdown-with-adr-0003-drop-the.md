---
id: T0030
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
# T0030: Align lint-markdown with ADR-0003: drop the --fix flag, add JSON check output, and rename its config to .lint-markdown.json

## Goals
Remove lint-markdown's `--fix` global flag, so the `fix` action is the only writing path, and give `fix` a `--dry-run` option.
Add `--format text|json` to `check`.
Rename the default config to `.lint-markdown.json`, reading `.markdown-lint.json` with a warning.
Keep exit codes 0 for clean, 1 for violations or failure, and 2 for invalid arguments.

## Task Execution Steps
- [ ] **[Read]**      Read the lint-markdown actions, the --fix flag handling, issue reporting, and profile config lookup.
- [ ] **[Implement]** Write failing tests for the removed flag, fix --dry-run, JSON output, and both config names.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Remove --fix, add fix --dry-run and check --format, and add the config fallback.
- [ ] **[Verify]**    Run the full suite and the installed integration commands from the technical spec.
- [ ] **[Doc]**       Update docs/tools/lint-markdown.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided on 2026-11-09 to rename .markdown-lint.json to .lint-markdown.json; legacy reading with a warning follows ADR-0003.
