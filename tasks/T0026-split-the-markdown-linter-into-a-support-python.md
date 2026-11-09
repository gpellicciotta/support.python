---
id: T0026
owner: ~
needs: [T0025]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0026: Split the Markdown linter into a support_python.markdown.lint engine and a support_python.tools.lint_markdown CLI module

## Goals
Move `src/support_python/markdown_lint.py` to `src/support_python/markdown/lint.py` with `git mv`.
Extract its CLI (harness, action handlers, `main`, and `TOOL_NAME`) into `src/support_python/tools/lint_markdown.py`.
Keep the linting API importable from `support_python.markdown` and the package root.
Repoint the `lint-markdown` console script, imports, tests, and docs, changing no behavior.

## Task Execution Steps
- [ ] **[Read]**      Read markdown_lint.py and classify every definition as engine or CLI per the technical spec.
- [ ] **[Implement]** Run the git mv commands, then move CLI tests into tests/tools/test_lint_markdown.py importing the new module.
- [ ] **[Verify]**    Run the suite and record the resulting import failures as red-phase proof.
- [ ] **[Implement]** Extract the CLI module and fix imports in registry, rules, package exports, and the console script.
- [ ] **[Verify]**    Reinstall editable, run the full suite, and compare lint-markdown check output before and after.
- [ ] **[Doc]**       Update docs/tools/lint-markdown.md, README.md, docs/index.md, CLAUDE.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The Markdown linter engine is library code; its command-line layer moves to support_python.tools.
