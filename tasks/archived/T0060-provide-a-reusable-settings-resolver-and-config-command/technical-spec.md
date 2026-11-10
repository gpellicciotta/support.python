# Reusable settings resolver and config command group

## Technical Specifications
### Context
- The [Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md) require this precedence: command-line options, environment variables, project file, user file, system file, defaults.
- They require JSON files with kebab-case keys, accepting underscores, and platform-specific user file locations.
- They require a `config` group with `path`, `list`, `names`, `get`, `set`, `delete`, and `edit`, where `list` is the default.
- T0057 adds kebab-case key normalization and T0058 adds `user_config_path`; this task builds on both.

### Required Behavior
Declaring settings:
- `Setting` declares a name, type, default, one-sentence description, and a `secret` flag.
- Supported types are string, integer, float, boolean, duration, list of strings, and dictionary.
- `SettingsSchema` holds the tool name, environment prefix, settings, and which file tiers the tool supports.

Resolving settings:
- The resolver returns each setting's effective value and source: `cli`, `env`, `project`, `user`, `system`, or `default`.
- Environment variable names derive from the prefix and key, with dashes and dots replaced by underscores.
- Dictionary settings merge key by key across tiers; other settings take the highest tier's value.
- Invalid values and unreadable files warn once on `stderr` and fall through to the next source.
- Unknown keys are ignored, and listed at `DEBUG` level.
- `--config {{path}}` replaces automatic file discovery.

The `config` command group, via `add_config_actions(harness, schema)`:
- `path` prints the selected file's path, or every tier's path with `--all`.
- `list`, the default, prints every setting with its value and source; `--verbose` adds type, default, and description.
- `names` prints setting names; `--verbose` adds type, default, and description.
- `get` prints only the value; `--source` or `--verbose` prints the full setting card.
- `set` validates, then writes the value with a kebab-case key, creating the file if missing.
- `delete` removes the setting from the selected file only.
- `edit` opens the selected file in `$VISUAL`, then `$EDITOR`, then the platform's default editor.
- `--user` and `--system` select the file on `path`, `set`, `delete`, and `edit`; the default is the project file, else the user file.
- Unknown setting names and invalid values exit 2.
- Every printing action supports `--format text|json`.
- Secret settings print as `***` in `list` and `get`.

### Design Decisions
- **[Decided]** Register `config` through the harness's existing action-group mechanism, as `DevopsCli` service groups do.
- **[Decided]** Keep the module stdlib-only, as the project's dependency policy requires.
- **[Decided]** Write files with stable key order and two-space indentation, preserving unrelated keys.

### Out of Scope
- Migrating existing tools onto the new module; each tool gets its own follow-up task.
- Comment-preserving formats such as TOML or YAML.

### Tests
- Unit: Each source wins over every lower source, and the reported source names the winning tier.
- Unit: Dictionary settings merge key by key across project and user files.
- Unit: An invalid environment value warns once and falls through to the file tiers.
- Unit: `config get` prints the bare value, and `config get --source` prints value, source, type, default, and description.
- Unit: `config set` rejects an invalid value with exit code 2 and leaves the file untouched.
- Unit: `config set --user` creates the user file with a kebab-case key; `config delete --user` removes it.
- Unit: `config list --format json` prints one JSON document, with secret values shown as `***`.
- Unit: `config edit` invokes `$VISUAL` before `$EDITOR`, with a stubbed launcher.
- Integration: A sample tool built on `ToolHarness` runs `config set`, `config get --source`, and `config path --all` end to end.

### Declared Files
- `src/support_python/config.py` (new)
- `src/support_python/cli.py`, only if the action-group mechanism needs a hook
- `src/support_python/__init__.py`
- `tests/test_config.py` (new)
- `tests/test_config_actions.py` (new)
- `docs/tutorials/configuration.md` (new) and `docs/requirements.md`
- `CHANGELOG.md`
