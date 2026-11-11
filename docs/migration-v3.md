# Migrating to support-python v3.0.0

Map every breaking change since v2.0.0 to its v3.0.0 replacement.
Version 3.0.0 moves tool settings onto the shared resolver and removes hardcoded schemas, salts, keys, and owners.
The `**[breaking]**` entries in the [CHANGELOG](../CHANGELOG.md) list each change.
Upgrading from v1.x? Read [migration-v2.md](migration-v2.md) first.

---

## Commands
| Tool                    | v2.0.0                                    | v3.0.0                                                           |
| :---------------------- | :---------------------------------------- | :--------------------------------------------------------------- |
| `processes`             | `kill` never asks                         | `kill` asks to confirm; `--yes` skips it, or exit `2` unattended |
| `agent-files`           | Own settings resolver                     | Shared resolver; see [Configuration Files](#configuration-files) |
| `lint-markdown`         | Own settings resolver                     | Shared resolver; see [Configuration Files](#configuration-files) |
| `git-repository-backup` | Own settings resolver                     | Shared resolver; see [Configuration Files](#configuration-files) |
| `lint-markdown`         | Resolves `gpellicciotta` links on disk    | Resolves only owners listed in `github-owners`, default none     |

---

## Configuration Files
- `git-repository-backup` warns, instead of exiting `2`, about unknown keys, malformed files, and invalid values.
  It also reads `GIT_REPOSITORY_BACKUP_*` variables and a system file.
- `lint-markdown` warns about malformed files and wrong-typed values.
  It reads `LINT_MARKDOWN_*` variables, a user file, and a system file, and replaces list settings as a whole across sources.
  The tool no longer reads the `{ "MD0xx": bool }` form of `rules`.
- `agent-files` warns about unknown keys, malformed files, and invalid values; empty strings and invalid tool definitions still exit `2`.
  It reads `AGENT_FILES_*` variables, a user file, and a system file, and merges `tools` across sources by tool name.
- Add `github-owners` to the `lint-markdown` configuration to keep checking `github.com/{{owner}}/...` links as sibling checkouts.

---

## Library API
Removed names and their replacements:

| v2.0.0 API                                                                                                   | v3.0.0 replacement                                       |
| :----------------------------------------------------------------------------------------------------------- | :------------------------------------------------------- |
| `transform_auth_users`, `transform_auth_credentials`, `transform_auth_tokens`, `transform_auth_applications` | Define the rules locally with `column_rules_transformer` |
| `transform_counters_users`, `transform_counters_webhooks`                                                    | Define the rules locally with `column_rules_transformer` |
| `STANDARD_SALT`, `DEFAULT_AES_KEY_HEX`                                                                       | Pass your own salt and AES key                           |

The SQL anonymizer no longer knows the `auth` and `counters` schemas:
- `anonymize_sql_stream(in, out, transformers)` and `anonymize_sql_string(sql, transformers)` require the `transformers` mapping.
  The `app`, `custom_password`, and `custom_transformers` parameters are gone; a transformer closes over its own password.
- `LocalMySqlManager(snapshot_transformers=...)` supplies the mapping; `snapshot_and_anonymize` logs an error and returns `None` without it.
- `snapshot_and_anonymize` drops `custom_password`, and `db snapshot` drops `--custom-password`.
- See [sql-anonymizer.md](tutorials/sql-anonymizer.md) for the rules the removed profiles applied.

The crypto helpers no longer ship a fixed salt or AES key:
- `STANDARD_SALT` and `DEFAULT_AES_KEY_HEX` are removed from `support_python` and `support_python.crypto`.
- `get_standard_password_hash(password, *, salt)` requires a non-empty `salt` as `bytes`; invalid values raise `ValueError`.
- `decrypt_property_value(val, key_hex)` requires a hex AES key of 16, 24, or 32 bytes; invalid values raise `ValueError`.
- `decrypt_property_value` raises `ImportError` for `aes:` values when `cryptography` is not installed.
- `decrypt_property_value` raises `ValueError` for malformed `aes:` values instead of returning the ciphertext.
- Output for the same explicit salt and key is unchanged.

Kept names changed behavior; update tests that assert exact output:
- `APP_AUTHOR` and `COPYRIGHT` default to `""`, omitting the ` - {copyright}` banner suffix when empty.
  Pass `copyright` to `ToolHarness` or `DevopsCli` to set a custom copyright banner.
  The five bundled tools and [devops.py](../scripts/devops.py) keep their banner through `TOOLS_COPYRIGHT`.
