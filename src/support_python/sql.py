"""Database snapshot anonymizer, sanitizer, and SQL tuple parser.

Provides streaming SQL tokenization and deterministic masking for sensitive PII and
credentials across SQL database dumps.
"""

from __future__ import annotations

import base64
import io
import re
from typing import Callable, Optional, TextIO

from .crypto import DEFAULT_TEST_PASSWORD, get_standard_password_hash

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


def _clean_val(val: str) -> str:
    """Strips quotes from a SQL string value."""
    s = val.strip()
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        inner = s[1:-1]
        return inner.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
    return s


def _clean_col(col: str) -> str:
    return col.strip().strip("`'\"").lower()


def _clean_int(val: str) -> Optional[int]:
    val_clean = val.strip().strip("'\"")
    try:
        return int(val_clean)
    except ValueError:
        return None


def _sql_str(val: str) -> str:
    escaped = val.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


# =============================================================================
# Domain Transformers
# =============================================================================


def transform_auth_users(rows: list[list[str]], col_names: Optional[list[str]] = None) -> int:
    """Anonymize auth-schema users table rows in place.

    Replaces user names and email addresses with synthetic identifiers generated
    via :func:`get_anonymized_user_info`.

    Args:
        rows: List of parsed SQL row tuples to modify in place.
        col_names: Optional list of column names for dynamic column index mapping.

    Returns:
        Count of modified user rows.
    """
    if col_names is not None:
        lower_cols = [_clean_col(c) for c in col_names]
        id_idx = lower_cols.index("id") if "id" in lower_cols else None
        name_idx = lower_cols.index("name") if "name" in lower_cols else None
        email_idx = lower_cols.index("email") if "email" in lower_cols else None
    else:
        id_idx, name_idx, email_idx = 0, 1, 2

    modified = 0
    for row in rows:
        user_id = 0
        if id_idx is not None and len(row) > id_idx:
            user_id = _clean_int(row[id_idx]) or 0
        name, email = get_anonymized_user_info(user_id)
        if name_idx is not None and len(row) > name_idx:
            row[name_idx] = _sql_str(name)
        if email_idx is not None and len(row) > email_idx:
            row[email_idx] = _sql_str(email)
        modified += 1
    return modified


def transform_auth_credentials(
    rows: list[list[str]], col_names: Optional[list[str]] = None, standard_hash: Optional[str] = None
) -> int:
    """Anonymize auth-schema credentials table rows in place.

    Replaces password hashes with deterministic standard password hash and anonymizes
    federated identity subjects.

    Args:
        rows: List of parsed SQL row tuples to modify in place.
        col_names: Optional list of column names for dynamic column index mapping.
        standard_hash: Optional custom password hash string to apply.

    Returns:
        Count of modified credential rows.
    """
    if standard_hash is None:
        standard_hash = get_standard_password_hash()

    # In MySQL, credentials.data is stored as Base64-encoded ASCII bytes
    b64_password_hash = base64.b64encode(standard_hash.encode("ascii")).decode("ascii")

    if col_names is not None:
        lower_cols = [_clean_col(c) for c in col_names]
        type_idx = lower_cols.index("type") if "type" in lower_cols else None
        user_id_idx = (
            lower_cols.index("user-id")
            if "user-id" in lower_cols
            else (lower_cols.index("user_id") if "user_id" in lower_cols else None)
        )
        data_idx = lower_cols.index("data") if "data" in lower_cols else None
    else:
        type_idx, user_id_idx, data_idx = 1, 2, 3

    modified = 0
    for row in rows:
        if data_idx is not None and len(row) > data_idx:
            cred_type = _clean_val(row[type_idx]).lower() if (type_idx is not None and len(row) > type_idx) else "password"
            user_id = (_clean_int(row[user_id_idx]) or 0) if (user_id_idx is not None and len(row) > user_id_idx) else 0
            if cred_type == "password":
                row[data_idx] = _sql_str(b64_password_hash)
            elif cred_type == "federated-id":
                orig_data = _clean_val(row[data_idx])
                try:
                    decoded = base64.b64decode(orig_data, validate=True).decode("utf-8", errors="replace")
                    if ":" in decoded:
                        orig_data = decoded
                except Exception:
                    pass

                if ":" in orig_data:
                    prefix_part, _ = orig_data.rsplit(":", 1)
                    fed_val = f"{prefix_part}:anon-sub-{user_id}"
                else:
                    fed_val = f"google:anon-sub-{user_id}"
                row[data_idx] = _sql_str(base64.b64encode(fed_val.encode("utf-8")).decode("ascii"))
            modified += 1
    return modified


def transform_auth_applications(rows: list[list[str]], col_names: Optional[list[str]] = None) -> int:
    """Anonymize auth-schema applications table rows in place by clearing application secrets.

    Args:
        rows: List of parsed SQL row tuples to modify in place.
        col_names: Optional list of column names for dynamic column index mapping.

    Returns:
        Count of modified application rows.
    """
    if col_names is not None:
        lower_cols = [_clean_col(c) for c in col_names]
        secret_idx = (
            lower_cols.index("app-secret")
            if "app-secret" in lower_cols
            else (lower_cols.index("app_secret") if "app_secret" in lower_cols else None)
        )
    else:
        secret_idx = 6

    modified = 0
    for row in rows:
        if secret_idx is not None and len(row) > secret_idx:
            row[secret_idx] = "NULL"
            modified += 1
    return modified


def transform_counters_users(rows: list[list[str]], col_names: Optional[list[str]] = None) -> int:
    """Anonymize counters-schema users table rows in place.

    Args:
        rows: List of parsed SQL row tuples to modify in place.
        col_names: Optional list of column names for dynamic column index mapping.

    Returns:
        Count of modified counter user rows.
    """
    if col_names is not None:
        lower_cols = [_clean_col(c) for c in col_names]
        id_idx = lower_cols.index("id") if "id" in lower_cols else None
        name_idx = lower_cols.index("name") if "name" in lower_cols else None
        email_idx = lower_cols.index("email") if "email" in lower_cols else None
        auth_user_id_idx = (
            lower_cols.index("auth-user-id")
            if "auth-user-id" in lower_cols
            else (lower_cols.index("auth_user_id") if "auth_user_id" in lower_cols else None)
        )
    else:
        id_idx, name_idx, email_idx, auth_user_id_idx = 0, 1, 2, 8

    modified = 0
    for row in rows:
        user_id = _clean_int(row[id_idx]) if (id_idx is not None and len(row) > id_idx) else 0
        auth_id = None
        if auth_user_id_idx is not None and len(row) > auth_user_id_idx and row[auth_user_id_idx].upper() != "NULL":
            auth_id = _clean_int(row[auth_user_id_idx])
        if auth_id is None:
            auth_id = user_id or 0

        name, email = get_anonymized_user_info(auth_id)
        if name_idx is not None and len(row) > name_idx:
            row[name_idx] = _sql_str(name)
        if email_idx is not None and len(row) > email_idx:
            row[email_idx] = _sql_str(email)
        modified += 1
    return modified


def transform_counters_webhooks(rows: list[list[str]], col_names: Optional[list[str]] = None) -> int:
    """Anonymize counters-schema webhooks table rows in place.

    Replaces target URLs with synthetic URLs and replaces secrets with synthetic tokens.

    Args:
        rows: List of parsed SQL row tuples to modify in place.
        col_names: Optional list of column names for dynamic column index mapping.

    Returns:
        Count of modified webhook rows.
    """
    if col_names is not None:
        lower_cols = [_clean_col(c) for c in col_names]
        id_idx = lower_cols.index("id") if "id" in lower_cols else None
        url_idx = (
            lower_cols.index("target-url")
            if "target-url" in lower_cols
            else (lower_cols.index("target_url") if "target_url" in lower_cols else None)
        )
        secret_idx = lower_cols.index("secret") if "secret" in lower_cols else None
    else:
        id_idx, url_idx, secret_idx = 0, 3, 4

    modified = 0
    for row in rows:
        webhook_id = (_clean_int(row[id_idx]) or 0) if (id_idx is not None and len(row) > id_idx) else 0
        if url_idx is not None and len(row) > url_idx:
            row[url_idx] = _sql_str(f"https://example.local/webhook/anon-{webhook_id}")
        if secret_idx is not None and len(row) > secret_idx:
            row[secret_idx] = _sql_str(f"anon-secret-{webhook_id}")
        modified += 1
    return modified


def transform_auth_tokens(rows: list[list[str]], col_names: Optional[list[str]] = None) -> int:
    """Anonymize tokens (both auth and counters services) in place with synthetic Base64 data.

    Args:
        rows: List of parsed SQL row tuples to modify in place.
        col_names: Optional list of column names for dynamic column index mapping.

    Returns:
        Count of modified token rows.
    """
    if col_names is not None:
        lower_cols = [_clean_col(c) for c in col_names]
        id_idx = lower_cols.index("id") if "id" in lower_cols else None
        data_idx = lower_cols.index("data") if "data" in lower_cols else None
    else:
        id_idx, data_idx = 0, 3

    modified = 0
    for row in rows:
        if data_idx is not None and len(row) > data_idx:
            token_id = (_clean_int(row[id_idx]) or 0) if (id_idx is not None and len(row) > id_idx) else 0
            b64_token = base64.b64encode(f"anon-token-{token_id}".encode("utf-8")).decode("ascii")
            row[data_idx] = _sql_str(b64_token)
            modified += 1
    return modified


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
    app: str = "auth",
    custom_password: Optional[str] = None,
    custom_transformers: Optional[dict[str, TableTransformer]] = None,
) -> dict[str, int]:
    """Reads a SQL dump stream, rewrites INSERT statements for sensitive tables,
    and writes the anonymized SQL to output_stream.

    Args:
        input_stream: Readable text stream containing the SQL dump.
        output_stream: Writable text stream to receive the anonymized SQL.
        app: Application schema profile ('auth', 'counters', or custom).
        custom_password: Optional plain-text password to hash into credentials.
        custom_transformers: Optional mapping of table_name -> callable(rows, col_names) -> count.

    Returns:
        A dictionary mapping modified table names to counts of modified rows.
    """
    app_lower = app.lower() if app else ""
    stats: dict[str, int] = {}
    standard_hash = get_standard_password_hash(custom_password or DEFAULT_TEST_PASSWORD)

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
                    app_lower,
                    standard_hash,
                    stats,
                    custom_transformers,
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
                    app_lower,
                    standard_hash,
                    stats,
                    custom_transformers,
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
            app_lower,
            standard_hash,
            stats,
            custom_transformers,
        )

    return stats


def _process_and_write_insert(
    output_stream: TextIO,
    prefix: str,
    table_name: str,
    col_names: Optional[list[str]],
    values_str: str,
    app: str,
    standard_hash: str,
    stats: dict[str, int],
    custom_transformers: Optional[dict[str, TableTransformer]] = None,
) -> None:
    rows = parse_sql_row_tuples(values_str)
    count = 0

    if custom_transformers and table_name in custom_transformers:
        count = custom_transformers[table_name](rows, col_names)
    elif app == "auth":
        if table_name == "users":
            count = transform_auth_users(rows, col_names)
        elif table_name == "credentials":
            count = transform_auth_credentials(rows, col_names, standard_hash)
        elif table_name == "tokens":
            count = transform_auth_tokens(rows, col_names)
        elif table_name == "applications":
            count = transform_auth_applications(rows, col_names)
    elif app == "counters":
        if table_name == "users":
            count = transform_counters_users(rows, col_names)
        elif table_name == "tokens":
            count = transform_auth_tokens(rows, col_names)
        elif table_name == "webhooks":
            count = transform_counters_webhooks(rows, col_names)

    if count > 0:
        stats[table_name] = stats.get(table_name, 0) + count

    new_values = format_sql_row_tuples(rows)
    output_stream.write(f"{prefix}{new_values};\n")


def anonymize_sql_string(
    sql: str,
    app: str = "auth",
    custom_password: Optional[str] = None,
    custom_transformers: Optional[dict[str, TableTransformer]] = None,
) -> tuple[str, dict[str, int]]:
    """Convenience helper to anonymize a SQL string in memory.

    Args:
        sql: Input SQL text string.
        app: Application schema profile ('auth', 'counters', or custom).
        custom_password: Optional plain-text password to hash into credentials.
        custom_transformers: Optional mapping of table_name -> callable(rows, col_names) -> count.

    Returns:
        A tuple of (anonymized_sql_string, stats_dict).
    """
    in_buf = io.StringIO(sql)
    out_buf = io.StringIO()
    stats = anonymize_sql_stream(
        in_buf,
        out_buf,
        app=app,
        custom_password=custom_password,
        custom_transformers=custom_transformers,
    )
    return out_buf.getvalue(), stats


__all__ = [
    "TableTransformer",
    "anonymize_sql_stream",
    "anonymize_sql_string",
    "format_sql_row_tuples",
    "get_anonymized_user_info",
    "parse_sql_row_tuples",
    "transform_auth_applications",
    "transform_auth_credentials",
    "transform_auth_tokens",
    "transform_auth_users",
    "transform_counters_users",
    "transform_counters_webhooks",
]
