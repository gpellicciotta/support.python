---
id: T0007
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0007: Add ANSI-aware Markdown table helpers

## Goals
Add ANSI-aware Markdown table helpers to support_python, extracted from the plan project's `utils/markdown.py` table section. Scope: strip_ansi, visible_width, delimiter-pipe and row splitting, delimiter-row detection, aligned table formatting, table-block reformatting, and alignment checking. Out of scope: convert_json_to_terminal_markdown. Do not shadow tables.format_table.

## Task Execution Steps
- [ ] **[Read]**      Read plan's table helpers, this repo's tables.format_table, and dev-guidelines' lint-markdown.py table checks.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement markdown.py and re-export its public symbols from the package root.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
