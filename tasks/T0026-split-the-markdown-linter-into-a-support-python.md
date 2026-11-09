---
id: T0026
owner: "@gemini"
session: antigravity-20261109-eac155
needs: []
branch: task/T0026-split-the-markdown-linter-into-a-support-python
worktree: .plan/work/T0026-split-the-markdown-linter-into-a-support-python
status: active
started_at: "2026-11-09T20:47:53Z"
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
- [x] **[Read]**      Read markdown_lint.py and classify every definition as engine or CLI per the technical spec.
- [x] **[Implement]** Run the git mv commands, then move CLI tests into tests/tools/test_lint_markdown.py importing the new module.
- [x] **[Verify]**    Run the suite and record the resulting import failures as red-phase proof.
- [x] **[Implement]** Extract the CLI module and fix imports in registry, rules, package exports, and the console script.
- [x] **[Verify]**    Reinstall editable, run the full suite, and compare lint-markdown check output before and after.
- [x] **[Doc]**       Update docs/tools/lint-markdown.md, README.md, docs/index.md, CLAUDE.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The Markdown linter engine is library code; its command-line layer moves to support_python.tools.

- [2026-11-09] **[Read]**
  Classified markdown_lint.py into engine (MarkdownLinter, LintIssue, file discovery, table/fix helpers) and CLI (TOOL_NAME, build_harness, main, action handlers, parser setup).

- [2026-11-09] **[Verify]**
  Captured red-phase import failures after git mv and test split (ImportError on support_python.tools.lint_markdown and ModuleNotFoundError on support_python.markdown_lint).

- [2026-11-09] **[Implement]**
  Extracted CLI to support_python.tools.lint_markdown, kept engine in support_python.markdown.lint, re-exported linting API, and updated tests including undeclared tests/test_console_scripts.py and tests/test_markdown_profiles.py.

- [2026-11-09] **[Doc]**
  Updated docs/tools/lint-markdown.md, docs/index.md, README.md, CLAUDE.md, and CHANGELOG.md (v2.0.6-pre).

- [2026-11-09] **[Verify]**
  Recorded task outcomes.
  - Files touched: 16.
  - Lines touched: 1226.
  - Reopenings: 0.

- [2026-11-09] **[Verify]**
  Verified editable install, full pytest suite (698 passed, task-116), ruff checks, and pre/post-split lint-markdown output (recount: 16 files, 1226 lines).

