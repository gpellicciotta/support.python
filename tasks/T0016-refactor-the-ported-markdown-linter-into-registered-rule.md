---
id: T0016
owner: ~
needs: [T0014]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0016: Refactor the ported Markdown linter into registered rule classes with loadable profiles

## Goals
Split the `MarkdownLinter` if-ladder into small rule classes in a `support_python.markdown` package with a rule registry.
Keep every `MD0xx` ID and message stable.
Add profiles loaded from `.markdown-lint.json`: a default profile with the generic rules and a `dev-guidelines` profile enabling `MD015` and the historical-task logic.
Prerequisite: T0014 merged.

Completion check: the ported tests pass unchanged, and profile tests pass.
Size estimate: 10 files, 900 lines.
Size note: Above the typical line because rule classes replace one 1,600-line module; no behavior changes beyond profile loading, so output stays comparable with T0014.

## Task Execution Steps
- [ ] **[Read]**      List every MD rule, its trigger conditions, and its dependencies on shared linter state.
- [ ] **[Implement]** Author failing tests for the registry, profile loading, and the dev-guidelines profile.
- [ ] **[Verify]**    Run the new tests and confirm they fail for the expected reasons.
- [ ] **[Implement]** Create the markdown package, registry, and rule classes while keeping existing tests green.
- [ ] **[Implement]** Add JSON profile loading and the default and dev-guidelines profiles.
- [ ] **[Verify]**    Run the full suite and diff linter output against T0014 on dev-guidelines.
- [ ] **[Doc]**       Document profiles in docs and update CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.
