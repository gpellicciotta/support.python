# Markdown Tables and Linting

`support_python.markdown` formats Markdown tables and lints Markdown files; all symbols below are re-exported from `support_python`:
- [tables.py](../../src/support_python/markdown/tables.py): ANSI-aware GitHub Flavored Markdown table helpers, using only the standard library.
  They leave `support_python.tables.format_table` unchanged.
- [lint.py](../../src/support_python/markdown/lint.py), [registry.py](../../src/support_python/markdown/registry.py), [rules.py](../../src/support_python/markdown/rules.py), and [profiles.py](../../src/support_python/markdown/profiles.py): `MarkdownLinter`, `LintIssue`, `RuleRegistry`, `LintProfile`, and `load_profile`.
- [plugins.py](../../src/support_python/markdown/plugins.py): extra rules loaded from plugin files or modules.

The `lint-markdown` command-line tool builds on the linter; see [lint-markdown.md](../tools/lint-markdown.md) for its actions, profiles, configuration, and rule plugins.

## Table helpers

```python
from support_python import (
    check_table_alignment,
    format_markdown_table,
    format_markdown_table_block,
    strip_ansi,
    visible_width,
)

table = format_markdown_table(["Name", "Score"], [["\x1b[32mAlice\x1b[0m", "100"]], alignments=["left", "right"])
issues = check_table_alignment(table)
```

- `strip_ansi(text)` removes ANSI CSI escape sequences, and `visible_width(text)` returns the stripped character count.
- `find_delimiter_pipes(line)` finds unescaped pipe indices outside backtick code spans, and `split_table_row(line)` returns trimmed cells.
- `is_table_delimiter_row(line)` validates GitHub Flavored Markdown separator rows such as `:---`, `:---:`, and `---:`.
- `format_markdown_table(headers, rows, alignments=None)` formats aligned GFM tables using visible cell widths.
- `format_markdown_table_block(table_lines)` reformats raw table lines in place while preserving leading blockquote prefixes.
- `check_table_alignment(content)` returns `TableAlignmentIssue` entries for any table rows with misaligned delimiter pipes.

## Linter
`load_profile` returns a built-in profile by name (`default` or `dev-guidelines`), or loads a `.lint-markdown.json` file.
`MarkdownLinter` lints and fixes content in memory; `lint_content` returns `LintIssue` records with line, column, rule, and message:

```python
from pathlib import Path

from support_python import MarkdownLinter, load_profile

linter = MarkdownLinter(offline=True, profile=load_profile(profile="default"))
issues = linter.lint_content(Path("notes.md"), b"# Notes\n\nTrailing space   \n")
for issue in issues:
    print(f"{issue.line_number}:{issue.column_number} {issue.rule_id} {issue.message}")
fixed = linter.fix_content(Path("notes.md"), b"# Notes\n\nTrailing space   \n")  # b"# Notes\n\nTrailing space\n"
```
