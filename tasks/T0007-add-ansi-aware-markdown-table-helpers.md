---
id: T0007
owner: "@gemini"
session: antigravity-20261107-c21e75
needs: []
branch: task/T0007-add-ansi-aware-markdown-table-helpers
worktree: .plan/work/T0007-add-ansi-aware-markdown-table-helpers
status: active
started_at: "2026-11-07T13:13:00Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0007: Add ANSI-aware Markdown table helpers

## Goals
Add ANSI-aware Markdown table helpers to support_python, extracted from the plan project's `utils/markdown.py` table section. Scope: strip_ansi, visible_width, delimiter-pipe and row splitting, delimiter-row detection, aligned table formatting, table-block reformatting, and alignment checking. Out of scope: convert_json_to_terminal_markdown. Do not shadow tables.format_table.

## Task Execution Steps
- [x] **[Read]**      Read plan's table helpers, this repo's tables.format_table, and dev-guidelines' lint-markdown.py table checks.
- [x] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [x] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [x] **[Implement]** Implement markdown.py and re-export its public symbols from the package root.
- [x] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [x] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-07] **[Read]**
  Inspected plan's utils/markdown.py, support_python.tables.format_table, and dev-guidelines' lint-markdown.py; lint-markdown.py duplicates non-ANSI table helpers for follow-up migration in T0014/T0016.

- [2026-11-07] **[Implement]**
  Authored unit and integration tests for ANSI-aware Markdown table helpers in tests/test_markdown.py.

- [2026-11-07] **[Verify]**
  Confirmed tests/test_markdown.py fails with ImportError before implementing support_python.markdown.

- [2026-11-07] **[Implement]**
  Implemented support_python.markdown with ANSI-aware table formatting, splitting, and alignment checks, and re-exported public symbols from support_python.

- [2026-11-07] **[Verify]**
  Verified test suite and linters pass cleanly.
  - 7 new tests in test_markdown.py passed.
  - 495 passed, 3 skipped in full pytest suite.
  - ruff check and ruff format --check passed.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md, README.md, CLAUDE.md, and docs/index.md for support_python.markdown.

- [2026-11-07] **[Verify]**
  Recorded task outcomes. Size note: Single cohesive module extraction and unit test suite that must merge together.
  - Files touched: 7.
  - Lines touched: 626.
  - Reopenings: 0.

