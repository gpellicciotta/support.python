---
task: T0007
round: 1
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-07T13:30:10Z
reviewed_commit: "a3b82eb"
base_commit: "487c380"
branch: task/T0007-add-ansi-aware-markdown-table-helpers
---
# Review Findings: Task T0007 (Round 1)

## Summary
Approved. `support_python.markdown` delivers every in-scope helper from the goals:
- `strip_ansi` and `visible_width`
- `find_delimiter_pipes` and `split_table_row`
- `is_table_delimiter_row`
- `format_markdown_table` and `format_markdown_table_block`
- `check_table_alignment`

The code is a faithful extraction of plan's `utils/markdown.py` table section. Two intentional changes:
- The formatter is renamed to `format_markdown_table`, so `tables.format_table` is not shadowed. The integration test asserts this.
- `check_table_alignment` strips ANSI before measuring pipe positions, which is the correct ANSI-aware behavior.

`convert_json_to_terminal_markdown` stays out of scope.

Verification run in the worktree:
- `pytest`: 495 passed, 3 skipped (matches the Execution Log).
- `ruff check .`: passed.
- `ruff format --check .`: 73 files already formatted.

The 7 new tests cover every unit and integration case in `technical-spec.md`:
- Ragged rows, ANSI padding, and idempotent block reformatting.
- Blockquote prefix preservation.
- Frontmatter, comment, and fenced-code skipping.
- Mixed ANSI, escaped-pipe, and all-alignment round-trip.

`validation-proof.md` records the red-phase ImportError, then green-phase, full-suite, and lint output.

The docs are updated: CHANGELOG (under the existing `v1.0.10-pre` heading, which matches `pyproject.toml`), README, CLAUDE.md, and docs/index.md. The package root re-exports all nine public symbols. The commit message is one past-tense sentence with no trailer.

## Defects
None blocking. Non-blocking observations, both inherited from the plan source and documented in the tests:
- `visible_width` counts characters, not terminal cells, so wide CJK and emoji characters misalign.
- `format_markdown_table_block` silently truncates data cells beyond the header column count.

## Process Gaps
None. The task file has no inline `## Technical Specifications` section, but the companion `technical-spec.md` holds the tests, decisions, and declared files. The follow-up migration note for dev-guidelines' `lint-markdown.py` (T0014/T0016) is in the Execution Log.

## Required Rework
None.
