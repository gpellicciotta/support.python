# MD011 allows up to two trailing spaces

## Technical Specifications
### Evidence
- `MD011TrailingWhitespace.check` in `src/support_python/markdown/rules.py` flags any line ending in a space or tab.
- The `fix` path in `src/support_python/markdown/lint.py` calls `fixed_line.rstrip(" \t")`, removing hard line breaks.
- dev-guidelines files use two trailing spaces as deliberate hard line breaks, and their `.editorconfig` keeps them for `*.md`.

### Required Behavior
- MD011 accepts a line ending in one or two spaces.
- MD011 flags a line ending in three or more spaces, or in any tab, mixed with spaces or not.
- The issue message says that at most two trailing spaces are allowed.
- `fix` trims a run of three or more trailing spaces to exactly two.
- `fix` removes trailing tabs, together with any spaces mixed with them.
- `fix` leaves lines ending in one or two spaces unchanged.
- Whitespace-only lines are checked by the same rules.

### Design Decisions
- **[Decided]** Change the default behavior rather than adding an option, since Markdown itself defines the hard line break.

### Out of Scope
- Backslash hard line breaks and other Markdown rules.

### Tests
- Unit: Lines ending in one and in two spaces pass MD011.
- Unit: Lines ending in three spaces, in a tab, and in a space followed by a tab fail MD011.
- Unit: `fix` turns four trailing spaces into two, removes a trailing tab, and keeps two trailing spaces.
- Integration: `lint-markdown check` on a file with two-space hard line breaks reports no MD011 issue, and `fix --dry-run` plans no change.

### Declared Files
- `src/support_python/markdown/rules.py`
- `src/support_python/markdown/lint.py`
- `tests/test_markdown_lint.py`
- `tests/tools/test_lint_markdown.py`
- `docs/tools/lint-markdown.md` and `CHANGELOG.md`
