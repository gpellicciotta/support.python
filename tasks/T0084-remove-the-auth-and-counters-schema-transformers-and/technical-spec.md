### Declared Files
- src/support_python/sql.py
- src/support_python/__init__.py
- src/support_python/devops/services.py
- tests/test_sql.py
- tests/test_devops_service_actions.py
- docs/tutorials/sql-anonymizer.md
- docs/index.md
- docs/migration-v2.md
- CHANGELOG.md

### Changes
- `anonymize_sql_stream(input_stream, output_stream, transformers: Mapping[str, TableTransformer]) -> dict[str, int]`.
- `anonymize_sql_string(sql, transformers) -> tuple[str, dict[str, int]]`.
- Match table names case-insensitively; tables without a transformer pass through as today.
- Remove `app`, `custom_password`, and `custom_transformers`; passing them raises `TypeError`.
- Remove these names from `sql.py`, its `__all__`, and the package root:
  - `transform_auth_users`, `transform_auth_credentials`, `transform_auth_tokens`, `transform_auth_applications`
  - `transform_counters_users`, `transform_counters_webhooks`
- `sql.py` no longer imports `crypto`.
- Keep the mysqldump handling: the `SQL_MODE` prelude and the skipped `SQL_LOG_BIN` and `GTID_PURGED` lines.
- `LocalMySqlManager.__init__` gains `snapshot_transformers: Optional[Mapping[str, TableTransformer]] = None`.
- `snapshot_and_anonymize` gains `transformers=None`, falling back to `snapshot_transformers`.
  - With neither, it logs an error naming `snapshot_transformers` and returns `None` before dumping anything.
  - It drops `custom_password`; `app_name` only names the dumped database and the output file.
- `docs/index.md` stops describing the anonymizer as specific to `auth` and `counters`.
- `migration-v2.md` gets one row per removed name and parameter, pointing to `column_rules_transformer` and the tutorial.

### Tests
- Unit: `anonymize_sql_string(sql)` without `transformers` raises `TypeError`, and so does passing `app=`.
- Unit: the removed names are absent from `support_python` and `support_python.sql`.
- Unit: `snapshot_and_anonymize` without transformers returns `None`, logs the error, and starts no subprocess.
- Integration: Keep T0083's auth and counters rule sets in `tests/test_sql.py`.
  - Anonymize the sample dumps in `tests/fixtures/sql/` with them.
  - The output must match golden files captured from the old code before its removal.

Completion check: `.venv/Scripts/python -m pytest tests/test_sql.py tests/test_devops_service_actions.py` plus `python scripts/devops.py check`.
Mechanical command: golden files come from running the pre-removal `anonymize_sql_string` on the sample dumps; they are uncounted.
Size estimate: 9 files, 520 lines
Size note: The removal and its required `services.py` fix-up cannot merge separately; most changed lines are deletions.

### Notes
- Breaking v2 change: record it in both migration-v2.md and CHANGELOG.md.
- auth and counters.server pin support-python v1.0.0, so they keep working until they upgrade.
- Their backlog tasks track defining the rules locally with `column_rules_transformer`.
