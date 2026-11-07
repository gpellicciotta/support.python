### Declared Files
- src/support_python/markdown.py
- tests/test_markdown.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 7 files, 450 lines
Size note: Single cohesive module extraction and unit test suite that must merge together.

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: strip_ansi removes color codes; visible_width ignores them and counts wide characters as the source does.
- Unit: find_delimiter_pipes ignores pipes inside code spans and escaped pipes; split_table_row returns trimmed cells.
- Unit: is_table_delimiter_row accepts :---, ---:, :---: and rejects ordinary rows.
- Unit: The aligned formatter pads left, right, and center columns; format_markdown_table_block rewrites a misaligned block idempotently.
- Unit: check_table_alignment returns a TableAlignmentIssue per misaligned row and none for aligned tables.
- Integration: Format a mixed table (ANSI-colored cells, escaped pipes, all three alignments) from a Markdown string, then run check_table_alignment on the output and expect no issues.

Completion check: python -m pytest tests/test_markdown.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Public name for the aligned formatter avoids tables.format_table; pick a distinct name such as format_markdown_table.
- **[Decided]** If lint-markdown.py in dev-guidelines duplicates these functions, record that as a follow-up migration, not part of this task.
