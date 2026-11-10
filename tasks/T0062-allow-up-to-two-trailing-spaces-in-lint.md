---
id: T0062
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: active
started_at: "2026-11-10T11:25:08Z"
ended_at: —
review: agent
preview: none
protocol: adhoc
---
# T0062: Allow up to two trailing spaces in lint-markdown MD011, so Markdown hard line breaks pass and fix keeps them

## Goals
Markdown uses two trailing spaces as a hard line break, so `lint-markdown` must accept them.
MD011 flags any trailing space or tab today, and `lint-markdown fix` strips every trailing space.
Allow up to two trailing spaces; keep flagging longer runs and any trailing tab.

Specifications: [technical-spec.md](T0062-allow-up-to-two-trailing-spaces-in-lint/technical-spec.md).
Completion check: `python -m pytest tests/test_markdown_lint.py tests/tools/test_lint_markdown.py` and `ruff check src tests`
Size estimate: 5 files, 80 lines

## Task Execution Steps
- [ ] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [ ] **[Implement]** Make MD011 accept one or two trailing spaces and still flag three or more, or any tab.
- [ ] **[Implement]** Make `fix` trim longer runs to two spaces instead of stripping all trailing spaces.
- [ ] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [ ] **[Doc]**       Update the MD011 description, `docs/tools/lint-markdown.md`, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
