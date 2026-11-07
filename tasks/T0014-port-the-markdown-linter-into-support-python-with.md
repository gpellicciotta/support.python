---
id: T0014
owner: ~
needs: ['T0013']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0014: Port the Markdown linter into support_python unchanged with a lint markdown CLI and ported tests

## Goals
Copy dev-guidelines `scripts/lint-markdown.py` into `support_python.markdown_lint` unchanged apart from imports.
Expose it as `support-python lint markdown [paths] [--fix] [--offline]` with identical rules and output.
Rule classes and profiles follow in T0016.
Prerequisite: T0013 merged.

Completion check: the ported tests pass and `support-python lint markdown` reports the same issues as the original script on dev-guidelines.
Size estimate: 4 files, 60 hand-written lines plus mechanical copies.
Mechanical command: `Copy-Item {{dev-guidelines}}/scripts/lint-markdown.py src/support_python/markdown_lint.py`
Mechanical command: `Copy-Item {{dev-guidelines}}/scripts/tests/test_lint_markdown.py tests/test_markdown_lint.py`

## Task Execution Steps
- [ ] **[Read]**      Read lint-markdown.py imports and its harness usage to plan the import fixes.
- [ ] **[Implement]** Copy the linter and its tests, then fix imports so the tests collect and fail.
- [ ] **[Verify]**    Confirm the ported tests fail only on the missing CLI registration.
- [ ] **[Implement]** Register the lint markdown subcommand in support_python.cli.
- [ ] **[Verify]**    Run the full suite and compare output against the original script on dev-guidelines.
- [ ] **[Doc]**       Update CHANGELOG.md and docs with the lint markdown command.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.
