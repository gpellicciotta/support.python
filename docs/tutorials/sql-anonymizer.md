# SQL Snapshot Anonymizer

[sql.py](../../src/support_python/sql.py) provides streaming SQL tokenization and deterministic masking for database dumps.
It replaces raw PII, credentials, session tokens, and webhook secrets with deterministic synthetic data.
Built-in table profiles cover the `auth` and `counters` applications.
`anonymize_sql_string` and `anonymize_sql_stream` are re-exported from `support_python`.

## Example

```python
from support_python import anonymize_sql_stream, anonymize_sql_string

# In-memory SQL string anonymization
anon_sql, stats = anonymize_sql_string(raw_sql, app="auth")

# Streaming file-to-file pipeline
with open("dump.sql", "r", encoding="utf-8") as in_f, open("clean.sql", "w", encoding="utf-8") as out_f:
    stats = anonymize_sql_stream(in_f, out_f, app="counters")
```
