### Declared Files
- src/support_python/sql.py
- src/support_python/__init__.py
- tests/test_sql.py
- docs/tutorials/sql-anonymizer.md
- CHANGELOG.md

### API
- `sql_value(literal: str) -> Optional[str]`: unquote and unescape one parsed SQL literal; `NULL` in any case returns `None`.
- `sql_literal(value: Optional[Union[str, int]]) -> str`: `None` gives `NULL`, an `int` gives digits.
  - A `str` gives a single-quoted literal, escaped like today's `_sql_str`.
- `sql_int(literal: str) -> Optional[int]`: the integer value, or `None` for `NULL` and non-integers.
- `column_index(col_names: Optional[Sequence[str]], name: str, position: Optional[int] = None) -> Optional[int]`:
  - Match names case-insensitively, ignoring backticks and quotes, and treating `-` and `_` as equal.
  - Return `position` when `col_names` is `None`, and `None` when the column is absent.
- `RowView`: a read-only view of one parsed row that resolves columns through `column_index`.
  - Methods: `has(name)`, `raw(name)`, `text(name)`, and `int(name)`.
- `KEEP`: a sentinel a rule returns to leave its column unchanged.
- `ColumnRule`: `Callable[[RowView], object]` returning a `str`, `int`, `None`, or `KEEP`.
- `column_rules_transformer(rules: Mapping[str, ColumnRule], *, positions: Optional[Mapping[str, int]] = None) -> TableTransformer`:
  - `positions` gives fallback indexes for dumps without a column list, replacing today's hardcoded positions.
  - Rules read the original row values, never values rewritten by an earlier rule.
  - Returned values are encoded with `sql_literal`.
  - A row counts as modified when at least one rule column exists in it.
- Existing transformers keep their exact behavior; T0084 removes them.

### Tests
- Unit: `sql_value` and `sql_literal` round-trip quotes, backslashes, and `NULL`; `sql_int` rejects non-integers.
- Unit: `column_index` matches `auth-user-id` to `auth_user_id`, honors `position` without names, and returns `None` when absent.
- Unit: a rule returning `KEEP` leaves its value; rules read original values; modified-row counting follows the API definition.
- Integration: In `tests/test_sql.py`, build auth rules for `users`, `credentials`, `tokens`, and `applications` with the builder only.
  - Build counters rules for `users`, `tokens`, and `webhooks` the same way.
  - Anonymize a multi-table dump, with and without column lists, through `anonymize_sql_string(..., app="", custom_transformers=...)`.
  - Assert byte-identical output and equal stats versus `app="auth"` and `app="counters"`.

Completion check: `.venv/Scripts/python -m pytest tests/test_sql.py` plus `python scripts/devops.py check`.
Size estimate: 5 files, 380 lines

### Notes
- **[Decided]** Keep `get_anonymized_user_info` as a generic helper; it encodes no table schema.
- The credentials rule receives its password hash through a closure, because T0085 makes the salt an explicit argument.
- The sql-anonymizer.md examples become the migration recipe for the auth and counters backlog tasks.
- The user asked that the result stays usable by the auth and counters repositories and by other projects.
- Support Python 3.9: use `from __future__ import annotations` and `typing.Optional`/`Union`.
