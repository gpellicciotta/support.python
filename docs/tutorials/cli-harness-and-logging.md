# CLI Harness and Logging

These modules give every command-line tool the same action-oriented interface, logging format, and output helpers:
- [cli.py](../../src/support_python/cli.py): `ToolHarness`/`Action` and `get_full_version`/`resolve_build_metadata`.
- [logging.py](../../src/support_python/logging.py): `CliLogger`, `LogLevel`, and log-level and message formatting helpers.
- [tables.py](../../src/support_python/tables.py): tabular and JSON output formatting with `format_table`/`render_output`.
- [tokens.py](../../src/support_python/tokens.py): persistent session token storage with `FileTokenStore` and `TokenStore`.

All symbols are re-exported from `support_python`.

## Action-oriented CLI harness, tables, and token storage
- `support_python.cli` provides `ToolHarness`/`Action`: registered actions with handlers, a fallback action, an exit-code table, and startup/exit banners.
  `get_full_version`/`resolve_build_metadata` add build-metadata version suffixes.
- `support_python.tables` provides tabular output formatting (`format_table`/`render_output`).
- `support_python.tokens` provides persistent session token storage (`FileTokenStore`, `TokenStore`).

```python
from dataclasses import dataclass
from support_python import (
    FileTokenStore,
    ToolHarness,
    format_table,
    render_output,
)


# Action-oriented CLI harness with standard banners, help, version, and logging
harness = ToolHarness(name="my-tool", description="My tool description", version="1.0.0")
harness.add_action("sync", "synchronize local state", handler=lambda args, logger: 0)


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
