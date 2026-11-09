---
id: T0021
owner: ~
needs: []
branch: —
worktree: —
status: cancelled
started_at: —
ended_at: "2026-11-09T18:44:20Z"
review: agent
preview: none
protocol: standard
---
# T0021: Expose the Markdown linter as an installable lint-markdown console script

## Goals
Add a `lint-markdown = "support_python.markdown_lint:main"` entry under `[project.scripts]` in `pyproject.toml`.
After installing the package, `lint-markdown check --offline` must behave like `support-python lint markdown check --offline`.
dev-guidelines CI calls `lint-markdown check --offline` and relies on this entry point.

## Task Execution Steps
- [ ] **[Implement]** Add a test asserting the installed lint-markdown entry point resolves to support_python.markdown_lint:main.
- [ ] **[Verify]**    Run the new test and record its failure as red-phase proof.
- [ ] **[Implement]** Add the lint-markdown console script entry to pyproject.toml and reinstall the package.
- [ ] **[Verify]**    Run the full suite and lint-markdown check --offline from an installed environment.
- [ ] **[Doc]**       Document the lint-markdown command in docs/markdown-lint.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Requested by the user so dev-guidelines CI can call lint-markdown directly.

- [2026-11-09] **[Cancelled]**
  Superseded by T0024, which installs lint-markdown as a console script within the v2.0.0 tool restructuring.

