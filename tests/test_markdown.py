"""Unit and integration tests for support_python.markdown."""

from __future__ import annotations

import support_python
from support_python import (
    TableAlignmentIssue,
    check_table_alignment,
    find_delimiter_pipes,
    format_markdown_table,
    format_markdown_table_block,
    format_table,
    is_table_delimiter_row,
    split_table_row,
    strip_ansi,
    visible_width,
)
import support_python.tables as tables


def test_strip_ansi_and_visible_width() -> None:
    assert strip_ansi("plain text") == "plain text"
    assert visible_width("plain text") == 10

    colored = "\x1b[32mActive\x1b[0m"
    assert strip_ansi(colored) == "Active"
    assert visible_width(colored) == 6

    compound = "\x1b[1;31mError:\x1b[0m \x1b[4mFailed\x1b[0m"
    assert strip_ansi(compound) == "Error: Failed"
    assert visible_width(compound) == 13

    # Wide Unicode characters are counted by character length (len of stripped string) as in plan's source.
    wide_plain = "漢字🚀"
    wide_colored = "\x1b[36m漢字\x1b[0m🚀"
    assert strip_ansi(wide_colored) == wide_plain
    assert visible_width(wide_plain) == len(wide_plain) == 3
    assert visible_width(wide_colored) == len(wide_plain) == 3


def test_find_delimiter_pipes_and_split_table_row() -> None:
    simple = "| A | B | C |"
    assert find_delimiter_pipes(simple) == [0, 4, 8, 12]
    assert split_table_row(simple) == ["A", "B", "C"]

    complex_line = r"| `x | y` | ``a | `b` | c`` | a \| b | trimmed   |"
    pipes = find_delimiter_pipes(complex_line)
    assert len(pipes) == 5
    assert split_table_row(complex_line) == ["`x | y`", "``a | `b` | c``", r"a \| b", "trimmed"]

    assert find_delimiter_pipes("no pipes here") == []
    assert split_table_row("no pipes here") == []
    assert split_table_row("| single pipe") == []


def test_is_table_delimiter_row() -> None:
    assert is_table_delimiter_row("| :--- | ---: | :---: | --- |")
    assert is_table_delimiter_row("|:---|---:|:---:|---|")
    assert is_table_delimiter_row("| :- | -: | :-: | - |")

    assert not is_table_delimiter_row("| Name | Age | Role |")
    assert not is_table_delimiter_row("| :--- | not-a-delim | ---: |")
    assert not is_table_delimiter_row("| :: | --- |")
    assert not is_table_delimiter_row("---|---")
    assert not is_table_delimiter_row("")


def test_format_markdown_table_alignments_and_edge_cases() -> None:
    assert format_markdown_table([], []) == ""
    assert format_markdown_table(["Col A", "Column B"], []) == "| Col A | Column B |\n| :---- | :------- |"

    headers = ["ID", "Name", "Score"]
    rows = [
        ["1", "Alice", "100"],
        ["22", "Bob", "9.5"],
        ["333", "Charlie", "0.1"],
    ]
    table = format_markdown_table(headers, rows, alignments=["center", "left", "right"])
    assert table == "\n".join(
        [
            "|  ID | Name    | Score |",
            "| :-: | :------ | ----: |",
            "|  1  | Alice   |   100 |",
            "|  22 | Bob     |   9.5 |",
            "| 333 | Charlie |   0.1 |",
        ]
    )

    # Ragged rows: shorter rows padded, extra columns truncated
    ragged = format_markdown_table(
        ["Col1", "Col2", "Col3"],
        [["A"], ["B", "C"], ["D", "E", "F", "G"]],
    )
    assert ragged == "\n".join(
        [
            "| Col1 | Col2 | Col3 |",
            "| :--- | :--- | :--- |",
            "| A    |      |      |",
            "| B    | C    |      |",
            "| D    | E    | F    |",
        ]
    )

    # ANSI cells pad according to visible width
    ansi_table = format_markdown_table(
        ["Left", "Center", "Right"],
        [["\x1b[32mok\x1b[0m", "\x1b[33mhi\x1b[0m", "\x1b[31m7\x1b[0m"]],
        alignments=["left", "center", "right"],
    )
    assert ansi_table == "\n".join(
        [
            "| Left | Center | Right |",
            "| :--- | :----: | ----: |",
            "| \x1b[32mok\x1b[0m   |   \x1b[33mhi\x1b[0m   |     \x1b[31m7\x1b[0m |",
        ]
    )


def test_format_markdown_table_block_idempotent_and_preserves_prefix() -> None:
    raw_block = [
        "  > | ID | Task Description | Status | Align Left | Right Align |",
        "  > |:---:|:---|:-:|---|--:|",
        "  > | 1 | Short | `ready` | a | 100 |",
        "  > | 222 | Very long task description | `in_progress` | foo bar | 999999 |",
        "  > | 3 | Another item | `completed` | test | 0 |",
    ]
    pass1 = format_markdown_table_block(raw_block)
    assert pass1 != raw_block
    assert all(line.startswith("  > | ") for line in pass1)
    assert check_table_alignment(pass1) == []

    pass2 = format_markdown_table_block(pass1)
    assert pass2 == pass1

    pass3 = format_markdown_table_block(pass2)
    assert pass3 == pass1

    short_block = ["| Only one row |"]
    assert format_markdown_table_block(short_block) == short_block


def test_check_table_alignment_reports_misaligned_rows_and_ignores_non_tables() -> None:
    aligned_doc = """---
title: Frontmatter with | pipe | characters
---
# Heading

| ID  | Name    | Score |
| :-: | :------ | ----: |
|  1  | Alice   |   100 |
|  22 | Bob     |   9.5 |

> | Symbol | Status |
> | :----: | :----- |
> | `[ ]`  | ready  |

<!--
| Misaligned | in comment |
|:-|---|
| 1 | 2 |
-->

```markdown
| Misaligned | in fenced code |
|:-|---|
| 1 | 2 |
```
"""
    assert check_table_alignment(aligned_doc) == []

    misaligned_doc = "\n".join(
        [
            "# Header",
            "",
            "| Col A | Col B |",
            "|:-|---|",
            "| Value 1 | Short |",
            "| Col A | Col B |",
            "| Long Value 2 | Val |",
        ]
    )
    issues = check_table_alignment(misaligned_doc)
    assert [issue.line_number for issue in issues] == [4, 5, 7]
    for issue in issues:
        assert isinstance(issue, TableAlignmentIssue)
        assert issue.column_number == 1
        assert "not vertically aligned" in issue.message


def test_integration_mixed_ansi_escaped_pipes_and_alignments() -> None:
    raw_markdown = "\n".join(
        [
            "| Feature | Expression | Score |",
            "|:---|---:|:---:|",
            r"| \x1b[32mAlpha\x1b[0m | a \| b | \x1b[1;34m10\x1b[0m |".replace(r"\x1b", "\x1b"),
            "| \x1b[33mBeta-Long\x1b[0m | `x | y` | 250 |",
            r"| Gamma | c \| d \| e | \x1b[31m5\x1b[0m |".replace(r"\x1b", "\x1b"),
        ]
    )
    assert len(check_table_alignment(raw_markdown)) > 0

    formatted_lines = format_markdown_table_block(raw_markdown.splitlines())
    formatted_markdown = "\n".join(formatted_lines)

    assert check_table_alignment(formatted_markdown) == []
    assert check_table_alignment(formatted_lines) == []
    assert format_markdown_table_block(formatted_lines) == formatted_lines

    # Confirm tables.format_table is not shadowed at package root
    assert format_table is tables.format_table
    assert support_python.format_markdown_table is format_markdown_table
