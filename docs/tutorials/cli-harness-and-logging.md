# CLI Harness and Logging

These modules give every command-line tool the same action-oriented interface, logging format, and output helpers:
- [cli.py](../../src/support_python/cli.py): `ToolHarness`/`Action` and `get_full_version`/`resolve_build_metadata`.
- [logging.py](../../src/support_python/logging.py): `CliLogger`, `LogLevel`, and log-level and message formatting helpers.
- [tables.py](../../src/support_python/tables.py): tabular and JSON output formatting with `format_table`/`render_output`.
- [tokens.py](../../src/support_python/tokens.py): persistent session token storage with `FileTokenStore` and `TokenStore`.

All symbols are re-exported from `support_python`.

- `support_python.cli` provides `ToolHarness`/`Action`: registered actions with handlers, a fallback action, an exit-code table, and startup/exit banners.
  `APP_AUTHOR` and `COPYRIGHT` default to empty strings, so banners show `{name} v{version}` without a copyright suffix.
  Pass `copyright` to `ToolHarness` to include ` - {copyright}` in banners.
  A `fallback_action` runs when the first argument names no action, as in `tool --url x` or `tool target`.
  Leading options keep a named action: `tool --verbose list` runs `list`.
  `ToolHarness.add_format_option` adds `--format text|json`; with `json`, the action's `CliLogger` runs with `json_output` set.
  Its log messages then go to `stderr`, and only `emit`/`emit_json` write to `stdout`.
  `get_full_version`/`resolve_build_metadata` add build-metadata version suffixes.
  Installed tools derive metadata from install records, never enclosing repositories.
  Use `get_package_version` for consumer `__version__` values to preserve the `-pre` suffix.
  `ToolHarness` also maps a trailing `rc0` back to `-pre` automatically.
- `support_python.tables` provides tabular output formatting (`format_table`/`render_output`).
- `support_python.tokens` provides persistent session token storage (`FileTokenStore`, `TokenStore`).

```python
from dataclasses import dataclass
from support_python import (
    FileTokenStore,
    ToolHarness,
    format_table,
    get_package_version,
    render_output,
)

# Resolve package version restoring -pre suffix for in-development versions
__version__ = get_package_version("my-package")

# Action-oriented CLI harness with standard banners, help, version, and logging
harness = ToolHarness(name="my-tool", description="My tool description", version=__version__)
harness.add_action("sync", "synchronize local state", handler=lambda args, logger: 0)


# '--format json' reserves stdout for the JSON document; log messages move to stderr
def report(args, logger) -> int:
    logger.info("collecting")
    logger.emit_json({"ok": True}, indent=2)
    return 0


harness.add_action("report", "print a status report", handler=report, configure_parser=ToolHarness.add_format_option)


# Tabular output and JSON formatting
@dataclass
class Item:
    id: int
    name: str


render_output([Item(1, "Alpha"), Item(2, "Beta")], output_format="table")

# Persistent CLI session token store
store = FileTokenStore()
store.store_token("my-auth-token")
saved_token = store.load_token()
```

## CLI logging
`support_python.CliLogger` provides unified guideline-compliant logging for command-line tools.
It pairs with `resolve_log_level`, `normalize_log_level`, `format_invocation_start`, and `init_cli_logger`:

```python
import sys

from support_python import CliLogger, resolve_log_level

level = resolve_log_level(explicit_level=None, debug=False, default="INFO")
logger = CliLogger(log_path="run.log", log_level=level, verbose=True, origin="my-tool")
logger.log_start("my-tool", "1.0.0", sys.argv, {"key": "value"})
logger.info("Doing work")
logger.warning("Something looked off")
logger.emit("raw-stdout-line")
logger.log_end("done")
logger.close()
```
