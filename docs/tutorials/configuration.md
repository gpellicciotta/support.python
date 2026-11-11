# Configuration

[config.py](../../src/support_python/config.py) implements the dev-guidelines
[Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md).
Declare a tool's settings once, then resolve them and add the standard `config` command group.
It uses only the standard library; its symbols are re-exported from `support_python`.

## Declaring settings
```python
from support_python import Setting, SettingsSchema

SCHEMA = SettingsSchema(
    "my-tool",
    [
        Setting("retries", "integer", 3, "Number of retries."),
        Setting("timeout", "duration", 30.0, "Request timeout."),
        Setting("labels", "dict", {}, "Labels to attach."),
        Setting("token", "string", None, "API token.", secret=True),
    ],
)
```

- Types: `string`, `integer`, `float`, `boolean`, `duration` (resolves to seconds), `list` (of strings), and `dict`.
- Names are kebab-case; underscores are accepted.
- `aliases=("old-name",)` makes other file keys mean the setting; the setting's own key wins when a file has both.
- `normalize=convert` runs `convert(raw)` on each raw value before parsing; raise `ValueError` to reject a value. `config set` skips it.
- `env_prefix` defaults to the upper-cased tool name, so `retries` reads `MY_TOOL_RETRIES`.
- `tiers` limits the supported files; `project_dir`, `project_file`, `system_path`, `environ`, and `platform` override discovery.

## Resolving settings
```python
from support_python import resolve_settings

resolved = resolve_settings(SCHEMA, cli={"retries": args.retries}, config_path=args.config, logger=logger)
retries = resolved["retries"].value  # resolved["retries"].source is "cli", "env", "project", "user", "system", or "default"
```

Precedence, highest first:
1. `cli` values, where `None` means not given.
2. Environment variables, with an empty one treated as unset.
3. Project file `.my-tool.json` in the project directory.
4. User file `$XDG_CONFIG_HOME/my-tool/config.json`, `%APPDATA%/my-tool/config.json`, or `~/.config/my-tool/config.json`.
5. System file `%PROGRAMDATA%/my-tool/config.json` or `/etc/my-tool/config.json`.
6. Defaults.

- Dictionary settings merge key by key across all sources; other settings take the first valid value.
- An invalid value or unreadable file warns once and falls through. Unknown keys are listed at `DEBUG` level.
- `config_path` replaces file discovery and counts as the `project` source.

## The config command group
```python
from support_python import ToolHarness, add_config_actions

harness = ToolHarness("my-tool", "Does things.")
add_config_actions(harness, SCHEMA)
raise SystemExit(harness.run())
```

```text
my-tool config                          # same as: config list
my-tool config list --verbose           # adds type, default, and description
my-tool config names
my-tool config get retries              # bare value
my-tool config get retries --source     # full setting card
my-tool config set retries 5            # project file; add --user or --system
my-tool config delete retries --user
my-tool config path --all
my-tool config edit                     # $VISUAL, then $EDITOR, then the platform default
```

- `set` validates first; unknown names and invalid values exit 2 and leave files untouched.
- `set` and `delete` write kebab-case keys in sorted order with two-space indentation and keep unrelated keys.
- Secret settings print as `***` in `list` and `get`, in text and JSON.
- Every printing action supports `--format text|json`.
- Put options after the positional words. The group adds `--config PATH` and `get --source` unless the harness has a global option of that name; `get --verbose` always prints the card.
