---
id: T0033
owner: "@claude"
session: claude-20261110-40a558
needs: []
branch: task/T0033-let-lint-markdown-load-extra-rules-from-plugin
worktree: .plan/work/T0033-let-lint-markdown-load-extra-rules-from-plugin
status: active
started_at: "2026-11-10T01:42:05Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0033: Let lint-markdown load extra rules from plugin modules and list all active rules with a rules action

## Goals
Let `.lint-markdown.json` list rule plugins under a `plugins` key, and accept repeatable `--plugin PATH_OR_MODULE` options.
Load each plugin by calling its module-level `register(registry)` with the active `RuleRegistry`.
Report duplicate rule IDs and broken plugins as errors exiting 2.
Add a `rules` action listing every rule and its source, honoring `--format text|json`.
Document writing a plugin rule in `docs/tools/lint-markdown.md`.

## Task Execution Steps
- [x] **[Read]**      Read RuleRegistry, Rule, profile loading, and how enabled rule IDs are computed.
- [x] **[Implement]** Write failing tests for path and module plugins, error cases, profile toggles, and the rules action.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Add the plugin loader, the plugins config key, the --plugin option, and the rules action.
- [x] **[Verify]**    Run the full suite and the installed integration scenario from the technical spec.
- [x] **[Doc]**       Document plugin authoring in docs/tools/lint-markdown.md, and update README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User asked on 2026-11-09 that lint-markdown be easy to extend with additional rules; explicit plugin listing keeps it stdlib-only.

- [2026-11-10] **[Verify]**
  Red phase: tests/test_markdown_plugins.py failed collection with ModuleNotFoundError for support_python.markdown.plugins before implementation.

- [2026-11-10] **[Implement]**
  Added the plugin loader, plugins config key, repeatable --plugin option, and rules action with text and JSON output.

- [2026-11-10] **[Verify]**
  Full suite, ruff, and the installed integration scenario passed; evidence is in validation-proof.md.
  - 773 passed, 3 skipped.
  - Installed check exits 1 reporting X001.

- [2026-11-10] **[Doc]**
  Size note: 9 files and 598 lines exceed the typical line; tests are 288 lines, and splitting would leave untested code.
  - Undeclared file: CLAUDE.md architecture list gained plugins.py.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 9.
  - Lines touched: 598.
  - Reopenings: 0.

