"""ANSI-aware Markdown table formatting, row parsing, and column alignment validation."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence


_RE_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    """Remove ANSI CSI escape sequences from a string.

    Args:
        text: Input string that may contain ANSI escape sequences.

    Returns:
        String with ANSI escape sequences removed.
    """
    return _RE_ANSI.sub("", text)


def visible_width(text: str) -> int:
    """Calculate the visible character width of a string, ignoring ANSI escape codes.

    Args:
        text: Input string to measure.

    Returns:
        Number of visible characters after stripping ANSI escape codes.
    """
    return len(strip_ansi(text))


def _align_cell(text: str, width: int, align: str) -> str:
    """Align cell text within a given column width, accounting for ANSI escape sequences."""
    if "\x1b" not in text:
        if align == "center":
            return text.center(width)
        if align == "right":
            return text.rjust(width)
        return text.ljust(width)

    vis_w = visible_width(text)
    pad = max(0, width - vis_w)
    if align == "center":
        left = pad // 2 + (pad & width & 1)
        right = pad - left
        return f"{' ' * left}{text}{' ' * right}"
    if align == "right":
        return f"{' ' * pad}{text}"
    return f"{text}{' ' * pad}"


@dataclass(frozen=True)
class TableAlignmentIssue:
    """Represents a Markdown table formatting or column alignment violation.

    Attributes:
        line_number: 1-based line number of the misaligned table row.
        column_number: 1-based column number where the table row begins.
        message: Human-readable description of the alignment violation.
    """

    line_number: int
    column_number: int
    message: str


def _normalize_alignment(align: str | None) -> str:
    """Normalize alignment specifier to 'left', 'center', or 'right'."""
    if not align:
        return "left"
    clean = align.strip().lower()
    if clean in ("center", "c", ":center:") or (clean.startswith(":") and clean.endswith(":") and len(clean) >= 3):
        return "center"
    if clean in ("right", "r", ":right:") or (clean.endswith(":") and len(clean) >= 2):
        return "right"
    return "left"


def find_delimiter_pipes(line: str) -> list[int]:
    """Find character indices of unescaped, non-code-span table pipe delimiters.

    Args:
        line: Single Markdown line to scan.

    Returns:
        Sorted list of 0-based character indices where delimiter pipes occur.
    """
    pipes: list[int] = []
    in_code = False
    code_ticks = 0
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch == "`":
            start = i
            while i < n and line[i] == "`":
                i += 1
            tick_count = i - start
            if not in_code:
                in_code = True
                code_ticks = tick_count
            elif tick_count == code_ticks:
                in_code = False
                code_ticks = 0
            continue
        elif ch == "\\" and not in_code:
            i += 2
            continue
        elif ch == "|" and not in_code:
            pipes.append(i)
        i += 1
    return pipes


def split_table_row(line: str) -> list[str]:
    """Split a Markdown table row into stripped cell strings on unescaped pipe delimiters.

    Args:
        line: Single Markdown table row string.

    Returns:
        List of trimmed cell values, or an empty list if fewer than two delimiter pipes exist.
    """
    pipes = find_delimiter_pipes(line)
    if len(pipes) < 2:
        return []
    cells: list[str] = []
    for start, end in zip(pipes[:-1], pipes[1:]):
        cells.append(line[start + 1 : end].strip())
    return cells


def is_table_delimiter_row(line: str) -> bool:
    """Check whether a line is a valid GitHub Flavored Markdown table delimiter row.

    Args:
        line: Single Markdown line to inspect.

    Returns:
        True if the line contains at least one cell and every cell matches ``^:?-+:?$``.
    """
    cells = split_table_row(line)
    if not cells:
        return False
    return all(bool(re.match(r"^:?-+:?$", cell)) for cell in cells)


def format_markdown_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    alignments: Sequence[str] | None = None,
) -> str:
    """Format a GitHub Flavored Markdown table with vertically aligned columns and padded separators.

    Args:
        headers: Sequence of column header labels.
        rows: Sequence of rows, each containing cell string values.
        alignments: Optional sequence of alignment specifiers per column (``'left'``, ``'center'``,
            ``'right'``, or Markdown delimiter cells like ``':---:'``). Defaults to ``'left'``.

    Returns:
        Formatted multi-line Markdown table string, or ``""`` if ``headers`` is empty.
    """
    if not headers:
        return ""

    num_cols = len(headers)
    norm_alignments = [_normalize_alignment(alignments[i] if alignments and i < len(alignments) else None) for i in range(num_cols)]

    col_widths = [max(3, visible_width(str(h))) for h in headers]
    str_rows: list[list[str]] = []
    for row in rows:
        row_cells = [str(cell) for cell in row]
        while len(row_cells) < num_cols:
            row_cells.append("")
        str_rows.append(row_cells[:num_cols])
        for i, cell in enumerate(row_cells[:num_cols]):
            col_widths[i] = max(col_widths[i], visible_width(cell))

    header_cells = [_align_cell(str(h), w, align) for h, w, align in zip(headers, col_widths, norm_alignments)]
    header_line = "| " + " | ".join(header_cells) + " |"

    sep_cells: list[str] = []
    for align, w in zip(norm_alignments, col_widths):
        if align == "center":
            sep_cells.append(":" + "-" * max(1, w - 2) + ":")
        elif align == "right":
            sep_cells.append("-" * max(2, w - 1) + ":")
        else:
            sep_cells.append(":" + "-" * max(2, w - 1))
    sep_line = "| " + " | ".join(sep_cells) + " |"

    lines = [header_line, sep_line]
    for row in str_rows:
        formatted_cells = [_align_cell(cell, w, align) for cell, w, align in zip(row, col_widths, norm_alignments)]
        lines.append("| " + " | ".join(formatted_cells) + " |")

    return "\n".join(lines)


def format_markdown_table_block(table_lines: Sequence[str]) -> list[str]:
    """Reformat a sequence of Markdown table lines into vertically aligned table lines.

    Preserves any leading indentation and blockquote prefix from the first line.

    Args:
        table_lines: Sequence of raw lines comprising a single Markdown table block.

    Returns:
        List of reformatted, vertically aligned Markdown table lines.
    """
    if len(table_lines) < 2:
        return list(table_lines)

    prefix_match = re.match(r"^(\s*(?:>\s*)*)", table_lines[0])
    prefix = prefix_match.group(1) if prefix_match else ""

    headers = split_table_row(table_lines[0])
    delim_cells = split_table_row(table_lines[1])
    alignments = [_normalize_alignment(cell) for cell in delim_cells]

    data_rows = [split_table_row(line) for line in table_lines[2:]]

    formatted_table_str = format_markdown_table(headers, data_rows, alignments=alignments)
    formatted_lines = formatted_table_str.split("\n")

    if prefix:
        return [f"{prefix}{line}" for line in formatted_lines]
    return formatted_lines


def check_table_alignment(content: str | Sequence[str]) -> list[TableAlignmentIssue]:
    """Scan Markdown content for table blocks and report vertical alignment violations.

    A table is considered properly aligned when:
    1. Every line in the table block (header, separator, and data rows) has the same number of columns.
    2. Every column delimiter pipe (``'|'``) occurs at the exact same visible character index across all rows.
    3. Separator cells properly pad dashes and colons to span the full column width.

    Args:
        content: Markdown string or sequence of lines.

    Returns:
        List of ``TableAlignmentIssue`` instances for any misaligned table rows.
    """
    if isinstance(content, str):
        lines = content.splitlines()
    else:
        lines = list(content)

    issues: list[TableAlignmentIssue] = []
    in_code_block = False
    code_fence_char = ""
    code_fence_len = 0
    in_html_comment = False
    in_frontmatter = False

    re_code_fence = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")

    i = 0
    num_lines = len(lines)

    while i < num_lines:
        line = lines[i]
        unquoted = re.sub(r"^\s*(?:>\s*)+", "", line)

        # Frontmatter tracking
        if i == 0 and unquoted.strip() == "---":
            in_frontmatter = True
            i += 1
            continue
        if in_frontmatter:
            if unquoted.strip() == "---":
                in_frontmatter = False
            i += 1
            continue

        # Code block tracking
        fence_match = re_code_fence.match(unquoted)
        if fence_match:
            _, fence, _ = fence_match.groups()
            fence_char = fence[0]
            fence_count = len(fence)
            if not in_code_block:
                in_code_block = True
                code_fence_char = fence_char
                code_fence_len = fence_count
            else:
                if fence_char == code_fence_char and fence_count >= code_fence_len:
                    in_code_block = False
                    code_fence_char = ""
                    code_fence_len = 0
            i += 1
            continue

        if in_code_block:
            i += 1
            continue

        # HTML comments
        if "<!--" in unquoted and "-->" not in unquoted:
            in_html_comment = True
            i += 1
            continue
        if in_html_comment:
            if "-->" in unquoted:
                in_html_comment = False
            i += 1
            continue

        # Table detection
        pipes = find_delimiter_pipes(strip_ansi(line))
        if len(pipes) >= 2 and i + 1 < num_lines:
            next_line = lines[i + 1]
            if is_table_delimiter_row(strip_ansi(next_line)):
                table_line_indices = [i, i + 1]
                k = i + 2
                while k < num_lines:
                    k_line = lines[k]
                    k_unquoted = re.sub(r"^\s*(?:>\s*)+", "", k_line)
                    if not strip_ansi(k_unquoted).strip():
                        break
                    k_pipes = find_delimiter_pipes(strip_ansi(k_line))
                    if len(k_pipes) < 2:
                        break
                    table_line_indices.append(k)
                    k += 1

                expected_pipes = pipes
                for row_idx in table_line_indices:
                    row_line = lines[row_idx]
                    row_pipes = find_delimiter_pipes(strip_ansi(row_line))
                    if row_pipes != expected_pipes:
                        col = row_pipes[0] + 1 if row_pipes else 1
                        issues.append(
                            TableAlignmentIssue(
                                line_number=row_idx + 1,
                                column_number=col,
                                message="Markdown table columns and delimiter pipes are not vertically aligned",
                            )
                        )

                i = k
                continue

        i += 1

    return issues


__all__ = [
    "TableAlignmentIssue",
    "check_table_alignment",
    "find_delimiter_pipes",
    "format_markdown_table",
    "format_markdown_table_block",
    "is_table_delimiter_row",
    "split_table_row",
    "strip_ansi",
    "visible_width",
]
