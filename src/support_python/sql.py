"""Database snapshot anonymizer, sanitizer, and SQL tuple parser.

Provides streaming SQL tokenization and deterministic masking for sensitive PII and
credentials across SQL database dumps.
"""

from __future__ import annotations

import io
import re
from typing import Callable, Mapping, Optional, Sequence, TextIO, Union

# Type alias for custom table transformer functions: (rows, col_names) -> count_modified
TableTransformer = Callable[[list[list[str]], Optional[list[str]]], int]


def get_anonymized_user_info(auth_user_id: int) -> tuple[str, str]:
    """Generate deterministic name and email for an auth user ID across all services.

    Args:
        auth_user_id: Numeric user identifier. User ID 0 is mapped to admin credentials.

    Returns:
        A tuple of ``(display_name, email_address)`` containing synthetic user data.
    """
    if auth_user_id == 0:
        return "Admin User", "admin@anonymized.invalid"
    return f"Anonymized User {auth_user_id}", f"anon-user-{auth_user_id}@anonymized.invalid"


def parse_sql_row_tuples(values_str: str) -> list[list[str]]:
    """Parse a SQL VALUES expression into a list of row value lists.

    Handles escaped characters, quotes, and nested parentheses (e.g. ``(1, 'val'), (2, 'other')``).

    Args:
        values_str: String containing raw SQL tuple expressions from an INSERT statement.

    Returns:
        List of parsed rows, where each row is a list of unescaped column value strings.
    """
    tuples_raw: list[str] = []
    i = 0
    n = len(values_str)
    current: list[str] = []
    in_quote = False
    quote_char: Optional[str] = None
    escape = False
    depth = 0

    while i < n:
        c = values_str[i]
        if escape:
            current.append(c)
            escape = False
        elif c == "\\":
            current.append(c)
            escape = True
        elif in_quote:
            if c == quote_char:
                if i + 1 < n and values_str[i + 1] == quote_char:
                    current.append(c)
                    current.append(quote_char)
                    i += 1
                else:
                    in_quote = False
                    quote_char = None
            current.append(c)
        else:
            if c in ("'", '"'):
                in_quote = True
                quote_char = c
                current.append(c)
            elif c == "(":
                depth += 1
                current.append(c)
            elif c == ")":
                depth -= 1
                current.append(c)
                if depth == 0:
                    tuples_raw.append("".join(current).strip())
                    current = []
            elif depth > 0:
                current.append(c)
        i += 1

    rows: list[list[str]] = []
    for tup in tuples_raw:
        s = tup.strip()
        if s.startswith("(") and s.endswith(")"):
            s = s[1:-1].strip()
        rows.append(_parse_single_tuple(s))
    return rows


def _parse_single_tuple(tuple_content: str) -> list[str]:
    values: list[str] = []
    i = 0
    n = len(tuple_content)
    current: list[str] = []
    in_quote = False
    quote_char: Optional[str] = None
    escape = False

    while i < n:
        c = tuple_content[i]
        if escape:
            current.append(c)
            escape = False
        elif c == "\\":
            current.append(c)
            escape = True
        elif in_quote:
            if c == quote_char:
                if i + 1 < n and tuple_content[i + 1] == quote_char:
                    current.append(c)
                    current.append(quote_char)
                    i += 1
                else:
                    in_quote = False
                    quote_char = None
            current.append(c)
        else:
            if c in ("'", '"'):
                in_quote = True
                quote_char = c
                current.append(c)
            elif c == ",":
                values.append("".join(current).strip())
                current = []
            else:
                current.append(c)
        i += 1

    if current:
        values.append("".join(current).strip())

    return values


def format_sql_row_tuples(rows: list[list[str]]) -> str:
    """Format a list of parsed rows back into a SQL VALUES expression.

    Args:
        rows: List of row value lists, where each inner list contains SQL string literals or nulls.

    Returns:
        Formatted SQL VALUES comma-separated tuple string (e.g. ``(1, 'val'), (2, 'val2')``).
    """
    formatted_rows = [f"({', '.join(row)})" for row in rows]
    return ", ".join(formatted_rows)


def _sql_str(val: str) -> str:
    escaped = val.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


# =============================================================================
# SQL Value Helpers and Declarative Transformer Builder
# =============================================================================


class _KeepSentinel:
    """Sentinel returned by a column rule to leave the column value unchanged."""

    def __repr__(self) -> str:
        return "KEEP"


KEEP = _KeepSentinel()


def sql_value(literal: str) -> Optional[str]:
    """Unquote and unescape one parsed SQL literal.

    Args:
        literal: Raw SQL literal string (e.g. ``'hello'``, ``NULL``, ``123``).

    Returns:
        The unquoted and unescaped string, or ``None`` when the literal is SQL NULL.
    """
    if literal is None:
        return None
    s = literal.strip()
    if s.upper() == "NULL":
        return None
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        inner = s[1:-1]
        res: list[str] = []
        i = 0
        n = len(inner)
        while i < n:
            if inner[i] == "\\" and i + 1 < n:
                res.append(inner[i + 1])
                i += 2
            elif inner[i] == "'" and i + 1 < n and inner[i + 1] == "'":
                res.append("'")
                i += 2
            elif inner[i] == '"' and i + 1 < n and inner[i + 1] == '"':
                res.append('"')
                i += 2
            else:
                res.append(inner[i])
                i += 1
        return "".join(res)
    return s


def sql_literal(value: Optional[Union[str, int]]) -> str:
    """Format a Python value as a valid SQL literal.

    Args:
        value: None (emits NULL), an int (emits digits), or a str (emits escaped single-quoted literal).

    Returns:
        Formatted SQL literal string.

    Raises:
        TypeError: If value is not None, int (excluding bool), or str.
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        raise TypeError(f"Boolean values are not supported as SQL literals: {value!r}")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{escaped}'"
    raise TypeError(f"Unsupported SQL literal value type: {type(value).__name__}")


def sql_int(literal: str) -> Optional[int]:
    """Parse an integer from a SQL literal.

    Args:
        literal: Raw SQL literal string.

    Returns:
        The parsed integer, or ``None`` for NULL, non-integers, or invalid literals.
    """
    if literal is None:
        return None
    val = literal.strip()
    if val.upper() == "NULL":
        return None
    if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
        val = val[1:-1].strip()
    try:
        return int(val)
    except ValueError:
        return None


def _normalize_col_name(name: str) -> str:
    return name.strip().strip("`'\"").lower().replace("-", "_")


def column_index(
    col_names: Optional[Sequence[str]],
    name: str,
    position: Optional[int] = None,
) -> Optional[int]:
    """Resolve the 0-based index of a column by name or fallback position.

    Matches column names case-insensitively, ignoring backticks and quotes,
    and treating dashes (``-``) and underscores (``_``) as equal.

    Args:
        col_names: Sequence of column names from an INSERT statement, or None when absent.
        name: Name of the column to find.
        position: Optional fallback 0-based position to return when ``col_names`` is None.

    Returns:
        The matched column index in ``col_names``, or ``position`` if ``col_names`` is None,
        or ``None`` if ``col_names`` is provided but does not contain the column.
    """
    if col_names is None:
        return position
    target = _normalize_col_name(name)
    for idx, col in enumerate(col_names):
        if _normalize_col_name(col) == target:
            return idx
    return None


class RowView:
    """Read-only view of a parsed SQL row resolving columns by name or fallback position."""

    def __init__(
        self,
        row: Sequence[str],
        col_names: Optional[Sequence[str]] = None,
        positions: Optional[Mapping[str, int]] = None,
    ) -> None:
        """Wrap a row with optional column names and name-to-position fallbacks."""
        self._row = tuple(row)
        self._col_names = tuple(col_names) if col_names is not None else None
        self._positions = {_normalize_col_name(k): v for k, v in positions.items()} if positions is not None else None

    def _col_idx(self, name: str) -> Optional[int]:
        fallback_pos = None
        if self._positions is not None:
            fallback_pos = self._positions.get(_normalize_col_name(name))
        return column_index(self._col_names, name, position=fallback_pos)

    def has(self, name: str) -> bool:
        """Return True if the column exists in this row."""
        idx = self._col_idx(name)
        return idx is not None and 0 <= idx < len(self._row)

    def raw(self, name: str) -> Optional[str]:
        """Return the raw SQL literal string of the column, or None if absent."""
        idx = self._col_idx(name)
        if idx is not None and 0 <= idx < len(self._row):
            return self._row[idx]
        return None

    def text(self, name: str) -> Optional[str]:
        """Return the unquoted and unescaped text value of the column, or None if absent or NULL."""
        raw_val = self.raw(name)
        if raw_val is None:
            return None
        return sql_value(raw_val)

    def int(self, name: str) -> Optional[int]:
        """Return the integer value of the column, or None if absent, NULL, or non-integer."""
        raw_val = self.raw(name)
        if raw_val is None:
            return None
        return sql_int(raw_val)


# Type alias for declarative column rule callables
ColumnRule = Callable[[RowView], object]


def column_rules_transformer(
    rules: Mapping[str, ColumnRule],
    *,
    positions: Optional[Mapping[str, int]] = None,
) -> TableTransformer:
    """Build a TableTransformer from declarative per-column rules.

    Args:
        rules: Mapping of column_name -> rule_callable(RowView) -> (str | int | None | KEEP).
        positions: Optional mapping of column_name -> fallback 0-based index for dumps without column lists.

    Returns:
        A TableTransformer function modifying rows in place and returning count of modified rows.
    """
    positions_map = {_normalize_col_name(k): v for k, v in positions.items()} if positions is not None else None

    def transformer(rows: list[list[str]], col_names: Optional[list[str]] = None) -> int:
        resolved_rules: list[tuple[Optional[int], ColumnRule]] = []
        for col_name, rule in rules.items():
            pos = positions_map.get(_normalize_col_name(col_name)) if positions_map else None
            idx = column_index(col_names, col_name, position=pos)
            resolved_rules.append((idx, rule))

        modified_rows = 0
        for row in rows:
            row_has_rule_col = any(idx is not None and 0 <= idx < len(row) for idx, _ in resolved_rules)
            if not row_has_rule_col:
                continue

            view = RowView(row, col_names=col_names, positions=positions)
            staged: list[tuple[int, str]] = []
            for idx, rule in resolved_rules:
                if idx is not None and 0 <= idx < len(row):
                    res = rule(view)
                    if res is not KEEP:
                        staged.append((idx, sql_literal(res)))

            for idx, literal_str in staged:
                row[idx] = literal_str

            modified_rows += 1

        return modified_rows

    return transformer


# =============================================================================
# Core SQL Anonymizer Pipeline
# =============================================================================

#: Regular expression matching standard SQL INSERT and REPLACE statements with VALUES clauses.
INSERT_RE: re.Pattern[str] = re.compile(
    r"^(\s*(?:INSERT(?:\s+IGNORE)?|REPLACE)(?:\s+INTO)?\s+(?:[`'\"]?[a-zA-Z0-9_-]+[`'\"]?\.)?[`'\"]?([a-zA-Z0-9_-]+)[`'\"]?\s*(?:\(([^)]+)\))?\s*VALUES\s*)(.*)$",
    re.IGNORECASE | re.DOTALL,
)


def anonymize_sql_stream(
    input_stream: TextIO,
    output_stream: TextIO,
    transformers: Mapping[str, TableTransformer],
) -> dict[str, int]:
    """Reads a SQL dump stream, rewrites INSERT statements for sensitive tables,
    and writes the anonymized SQL to output_stream.

    Args:
        input_stream: Readable text stream containing the SQL dump.
        output_stream: Writable text stream to receive the anonymized SQL.
        transformers: Mapping of lowercase table_name -> callable(rows, col_names) -> count of modified rows.
            Tables without an entry pass through unchanged.

    Returns:
        A dictionary mapping modified table names to counts of modified rows.
    """
    stats: dict[str, int] = {}

    output_stream.write("/*!40101 SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;\n")

    in_multi_line_insert = False
    current_table = ""
    current_col_names: Optional[list[str]] = None
    current_prefix = ""
    statement_buffer: list[str] = []

    for line in input_stream:
        # Skip statements requiring elevated SUPER / SESSION_VARIABLES_ADMIN privileges
        if "SQL_LOG_BIN" in line or "GTID_PURGED" in line:
            continue

        if in_multi_line_insert:
            statement_buffer.append(line)
            stripped = line.rstrip()
            if stripped.endswith(";"):
                full_stmt = "".join(statement_buffer)
                full_vals = full_stmt[len(current_prefix) :].rstrip().rstrip(";")
                _process_and_write_insert(
                    output_stream,
                    current_prefix,
                    current_table,
                    current_col_names,
                    full_vals,
                    stats,
                    transformers,
                )
                in_multi_line_insert = False
                current_table = ""
                current_col_names = None
                current_prefix = ""
                statement_buffer = []
            continue

        m = INSERT_RE.match(line)
        if m:
            prefix = m.group(1)
            table_name = m.group(2).lower()
            cols_raw = m.group(3)
            col_names = [c.strip() for c in cols_raw.split(",")] if cols_raw else None
            rest = m.group(4)

            stripped = rest.rstrip()
            if stripped.endswith(";"):
                vals_part = stripped[:-1]
                _process_and_write_insert(
                    output_stream,
                    prefix,
                    table_name,
                    col_names,
                    vals_part,
                    stats,
                    transformers,
                )
            else:
                in_multi_line_insert = True
                current_prefix = prefix
                current_table = table_name
                current_col_names = col_names
                statement_buffer = [line]
        else:
            output_stream.write(line)

    if in_multi_line_insert and statement_buffer:
        full_stmt = "".join(statement_buffer)
        full_vals = full_stmt[len(current_prefix) :].rstrip().rstrip(";")
        _process_and_write_insert(
            output_stream,
            current_prefix,
            current_table,
            current_col_names,
            full_vals,
            stats,
            transformers,
        )

    return stats


def _process_and_write_insert(
    output_stream: TextIO,
    prefix: str,
    table_name: str,
    col_names: Optional[list[str]],
    values_str: str,
    stats: dict[str, int],
    transformers: Mapping[str, TableTransformer],
) -> None:
    rows = parse_sql_row_tuples(values_str)
    count = 0

    transformer = transformers.get(table_name)
    if transformer is not None:
        count = transformer(rows, col_names)

    if count > 0:
        stats[table_name] = stats.get(table_name, 0) + count

    new_values = format_sql_row_tuples(rows)
    output_stream.write(f"{prefix}{new_values};\n")


def anonymize_sql_string(
    sql: str,
    transformers: Mapping[str, TableTransformer],
) -> tuple[str, dict[str, int]]:
    """Convenience helper to anonymize a SQL string in memory.

    Args:
        sql: Input SQL text string.
        transformers: Mapping of lowercase table_name -> callable(rows, col_names) -> count of modified rows.

    Returns:
        A tuple of (anonymized_sql_string, stats_dict).
    """
    in_buf = io.StringIO(sql)
    out_buf = io.StringIO()
    stats = anonymize_sql_stream(in_buf, out_buf, transformers)
    return out_buf.getvalue(), stats


__all__ = [
    "ColumnRule",
    "KEEP",
    "RowView",
    "TableTransformer",
    "anonymize_sql_stream",
    "anonymize_sql_string",
    "column_index",
    "column_rules_transformer",
    "format_sql_row_tuples",
    "get_anonymized_user_info",
    "parse_sql_row_tuples",
    "sql_int",
    "sql_literal",
    "sql_value",
]
