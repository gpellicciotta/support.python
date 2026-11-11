# SQL Snapshot Anonymizer

[sql.py](../../src/support_python/sql.py) provides streaming SQL tokenization and deterministic masking for database dumps.
It replaces raw PII, credentials, session tokens, and webhook secrets with deterministic synthetic data.
The declarative builder creates custom table transformers from per-column rules.

## Core API
- `column_rules_transformer(rules, *, positions=None)`: builds a `TableTransformer` from column rules.
- `RowView`: read-only view of a parsed SQL row with `has`, `raw`, `text`, and `int` accessors.
- `KEEP`: sentinel returned by a rule to leave a column untouched.
- `sql_value(literal)`: unquotes and unescapes a SQL literal; returns `None` for SQL NULL.
- `sql_literal(value)`: formats `None` as `NULL`, integers as digits, and strings as escaped literals.
- `sql_int(literal)`: parses integer values, returning `None` for NULL or non-integers.
- `column_index(col_names, name, position=None)`: resolves column positions case-insensitively.

## Declarative Builder Examples

### Auth Application Profile
Rebuild the auth service rules using `column_rules_transformer`:

```python
import base64
from support_python import (
    KEEP,
    anonymize_sql_stream,
    column_rules_transformer,
    get_anonymized_user_info,
    get_standard_password_hash,
)

auth_transformers = {
    "users": column_rules_transformer(
        {
            "name": lambda r: get_anonymized_user_info(r.int("id") or 0)[0],
            "email": lambda r: get_anonymized_user_info(r.int("id") or 0)[1],
        },
        positions={"id": 0, "name": 1, "email": 2},
    ),
    "credentials": column_rules_transformer(
        {
            "data": lambda r: (
                base64.b64encode(get_standard_password_hash().encode("ascii")).decode("ascii")
                if (r.text("type") or "password").lower() == "password"
                else KEEP
            ),
        },
        positions={"type": 1, "user-id": 2, "data": 3},
    ),
    "tokens": column_rules_transformer(
        {
            "data": lambda r: base64.b64encode(f"anon-token-{r.int('id') or 0}".encode("utf-8")).decode("ascii"),
        },
        positions={"id": 0, "data": 3},
    ),
    "applications": column_rules_transformer(
        {"app-secret": lambda r: None},
        positions={"app-secret": 6},
    ),
}

with open("dump.sql", "r", encoding="utf-8") as in_f, open("clean.sql", "w", encoding="utf-8") as out_f:
    stats = anonymize_sql_stream(in_f, out_f, app="", custom_transformers=auth_transformers)
```

### Counters Application Profile
Rebuild the counters service rules using `column_rules_transformer`:

```python
import base64
from support_python import (
    anonymize_sql_stream,
    column_rules_transformer,
    get_anonymized_user_info,
)


def _counters_user(row):
    auth_id = row.int("auth-user-id")
    if auth_id is None:
        auth_id = row.int("id") or 0
    return get_anonymized_user_info(auth_id)


counters_transformers = {
    "users": column_rules_transformer(
        {
            "name": lambda r: _counters_user(r)[0],
            "email": lambda r: _counters_user(r)[1],
        },
        positions={"id": 0, "name": 1, "email": 2, "auth-user-id": 8},
    ),
    "tokens": column_rules_transformer(
        {
            "data": lambda r: base64.b64encode(f"anon-token-{r.int('id') or 0}".encode("utf-8")).decode("ascii"),
        },
        positions={"id": 0, "data": 3},
    ),
    "webhooks": column_rules_transformer(
        {
            "target-url": lambda r: f"https://example.local/webhook/anon-{r.int('id') or 0}",
            "secret": lambda r: f"anon-secret-{r.int('id') or 0}",
        },
        positions={"id": 0, "target-url": 3, "secret": 4},
    ),
}

with open("dump.sql", "r", encoding="utf-8") as in_f, open("clean.sql", "w", encoding="utf-8") as out_f:
    stats = anonymize_sql_stream(in_f, out_f, app="", custom_transformers=counters_transformers)
```
