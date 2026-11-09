---
id: T0033
owner: ~
needs: [T0030]
branch: —
worktree: —
status: ready
started_at: —
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
- [ ] **[Read]**      Read RuleRegistry, Rule, profile loading, and how enabled rule IDs are computed.
- [ ] **[Implement]** Write failing tests for path and module plugins, error cases, profile toggles, and the rules action.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Add the plugin loader, the plugins config key, the --plugin option, and the rules action.
- [ ] **[Verify]**    Run the full suite and the installed integration scenario from the technical spec.
- [ ] **[Doc]**       Document plugin authoring in docs/tools/lint-markdown.md, and update README.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User asked on 2026-11-09 that lint-markdown be easy to extend with additional rules; explicit plugin listing keeps it stdlib-only.
