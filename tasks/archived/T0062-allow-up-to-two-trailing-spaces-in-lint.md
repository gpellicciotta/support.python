---
id: T0062
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T11:25:08Z"
ended_at: "2026-11-10T11:39:25Z"
review: agent
preview: none
protocol: adhoc
review_status: approved
review_round: 1
reviewed_by: "@claude-code-reviewer"
completion-commit: b668ce460d2cf4c60a22622bc629a50bad623bd3
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
- [x] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [x] **[Implement]** Make MD011 accept one or two trailing spaces and still flag three or more, or any tab.
- [x] **[Implement]** Make `fix` trim longer runs to two spaces instead of stripping all trailing spaces.
- [x] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [x] **[Doc]**       Update the MD011 description, `docs/tools/lint-markdown.md`, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Verify]**
  Added failing tests, implemented MD011 and fix change, updated docs; full suite and ruff pass.
  - Files touched: 8.
  - Lines touched: 120.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-reviewer.

- [2026-11-10] **[Review]**
  Reviewer subagent approved the commit; recorded approval.

- [2026-11-10] **[Doc]**
  Added validation proof with test and lint output.

- [2026-11-10] **[Complete]**
  Task completed successfully.

