# Python Support Library

General-purpose Python support library and CLI, with as few third-party dependencies as possible.

Licensed under the [MIT License](LICENSE.md).

See also:
- [CHANGELOG](CHANGELOG.md)
- [Documentation index](docs/index.md)
- [PLAN](PLAN.md)

## Bootstrap

```bash
# Cross-platform (Windows/Linux/macOS): creates a venv, installs editable + dev extras,
# lints, tests, and builds
python scripts/bootstrap-dev-environment.py
```

See [docs/devops.md](docs/devops.md) for the full development and release workflow.

## Build

```bash
python -m pip install --upgrade build
python -m build
```

This creates both source (`dist/*.tar.gz`) and binary wheel (`dist/*.whl`) packages.
On GitHub pushes/PRs, the same artifacts are built (after lint and tests) by
`.github/workflows/python-package.yml`.

## Install CLI

```bash
python -m pip install .
support-python greet Alice
support-python --version
support-python --help
```

## Use from another Python project

```python
from support_python import format_support_message

print(format_support_message("Alice"))
```

## Shared CLI helpers, tabular output, and session storage

`support_python.cli` provides `build_action_parser`/`print_version`/`print_help`, `support_python.tables` provides
tabular output formatting (`format_table`/`render_output`), and `support_python.tokens` provides persistent
session token storage (`FileTokenStore`, `TokenStore`):

```python
from dataclasses import dataclass
from support_python import (
    FileTokenStore,
    build_action_parser,
    format_table,
    print_help,
    print_version,
    render_output,
)


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

This library's own `support-python` CLI (`greet`/`version`/`help` actions) is a reference implementation built on top of it:

```python
from support_python import build_action_parser, print_help, print_version

PROG, DESCRIPTION, ACTIONS = "my-tool", "My tool's description", ["run", "version", "help"]


def main(argv=None) -> int:
    parser = build_action_parser(PROG, DESCRIPTION, ACTIONS, default_action="run")
    args = parser.parse_args(argv)
    if args.help or args.action == "help":
        print_help(PROG, "1.0.0", DESCRIPTION, parser)
        return 0
    if args.version or args.action == "version":
        print_version(PROG, "1.0.0")
        return 0
    ...  # dispatch on args.action
    return 0
```

## Common script utilities

`support_python` provides focused modules for script and developer operations:

- `terminal`: `configure_utf8_output` for cross-platform console standard stream encoding.
- `version`: `get_project_version` for resolving version from Gradle properties or pyproject.toml.
- `net`: `is_port_in_use` for checking TCP socket availability.
- `env`: `read_env_file` for parsing `.env` or properties files.
- `crypto`: `get_standard_password_hash` and `decrypt_property_value` for credentials and properties.

```python
from support_python import (
    configure_utf8_output,
    decrypt_property_value,
    get_project_version,
    get_standard_password_hash,
    is_port_in_use,
    read_env_file,
)

# Ensure console standard streams encode UTF-8 correctly
configure_utf8_output()

# Resolve version from Gradle properties, build.gradle, or pyproject.toml
version = get_project_version()

# Check port availability
if not is_port_in_use(8080):
    print("Port 8080 is available")

# Parse .env or properties file
env_vars = read_env_file(".env")

# Compute standard password hash
password_hash = get_standard_password_hash("my-password")
```

## CLI logging

`support_python.CliLogger` provides guideline-compliant logging (`general-guidelines.md`'s
Logging section) for command-line tools, API-similar to the logging package in
support.java (`LogLevel` naming, `log`/`info`/`warning`/`debug` methods):

```python
from support_python import CliLogger

logger = CliLogger(log_path="run.log", verbose=True, origin="my-tool")
logger.log_start("my-tool", "1.0.0", sys.argv, {"key": "value"})
logger.info("Doing work")
logger.warning("Something looked off")
logger.log_end("done")
```

## REST client HTTP transport

`support_python.net` provides a stdlib-only HTTP transport for building REST API clients:
`Transport` (a protocol so tests can inject a stub instead of hitting a real server), `UrllibTransport`
(the default `urllib.request`-based implementation), `RawResponse` (status/headers/body plus `.text()`/
`.json()` helpers), and `build_query_string`. A non-2xx response is still a normal `RawResponse` — only a
genuine connectivity failure (unreachable host, timeout, DNS failure, ...) raises `TransportError`. Callers
can map response status codes onto the shared REST error hierarchy:

```python
from support_python import TransportError, UrllibTransport, build_query_string, map_error

transport = UrllibTransport()
try:
    response = transport.request("GET", f"https://api.example.com/things{build_query_string({'q': 'abc'})}")
except TransportError as e:
    ...  # unreachable host, timeout, DNS failure, ...
if response.status_code >= 400:
    raise map_error(response.status_code, response.text(), response.text())
```

## REST client error hierarchy and status mapping

`support_python.errors` provides a unified exception hierarchy and status-code mapping helper for REST clients:

```python
from support_python import (
    ApiError,
    AuthenticationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    map_error,
)

try:
    raise map_error(404, "Target resource not found")
except NotFoundError as e:
    print(f"Not found: {e.message}")
except ApiError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

## DevOps script helpers and environment managers

`support_python.devops` provides `run_step`, `CloudSqlProxyManager`, `LocalDockerManager`,
`LocalMySqlManager`, `LocalServerManager`, `LocalMailManager`, and `LocalVerifier` for local developer
orchestration and deployment scripts:

```python
from support_python import (
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMySqlManager,
    LocalServerManager,
    run_step,
)

# Manage Docker Engine & Desktop
docker_mgr = LocalDockerManager()
if docker_mgr.get_status() != "running":
    docker_mgr.start_desktop()

# Manage Isolated MySQL Container & Snapshots
# Passwords have no defaults: pass them or define MYSQL_PASSWORD / MYSQL_ROOT_PASSWORD in the env file.
mysql_mgr = LocalMySqlManager(container_name="app-local-mysql", port=3306, mysql_env_file="mysql.env")
mysql_mgr.ensure_running()

# The Cloud SQL instance (project:region:instance) is mandatory
proxy_mgr = CloudSqlProxyManager("my-project:my-region:my-instance")

# Manage Local Application Server Process
server_mgr = LocalServerManager(port=8080)
server_mgr.start(background=True)
```

## View Capture Engine and Static Server

`support_python.capture` provides browser screenshot automation (`ViewCaptureEngine`) and visual UI tour
orchestration (`run_tour`, `run_capture_cli`). Embedded static web serving is provided by
`support_python.httpd` (`EmbeddedStaticServer`, `StaticServerManager`).
Webapps can declare their view presets and drive screenshot capture and markdown tour reports (`ui-tour-report.md`)
with minimal boilerplate:

```python
from pathlib import Path
import sys
from support_python import CaptureAppConfig, PresetConfig, run_capture_cli

config = CaptureAppConfig(
    app_name="Example Auth",
    cli_name="capture-view",
    version="1.0.0",
    presets={
        "sign-in": PresetConfig(
            name="sign-in",
            path="/demo/sign-in-view-harness.html",
            default_output="docs/img/sign-in-view.png",
            desktop_viewport="1000x700",
            mobile_viewport="390x844",
            title="Sign In View",
            description="Centralized sign-in card supporting credentials and social logins.",
        ),
    },
    webapp_dir=Path(__file__).resolve().parent.parent / "webapp",
)

if __name__ == "__main__":
    sys.exit(run_capture_cli(config))
```

## SQL Snapshot Anonymizer

`support_python.sql` provides streaming SQL tokenization and deterministic masking for database dumps.
It replaces raw PII, credentials, session tokens, and webhook secrets with deterministic synthetic data for the
built-in `auth` and `counters` table profiles:

```python
from support_python import anonymize_sql_stream, anonymize_sql_string

# In-memory SQL string anonymization
anon_sql, stats = anonymize_sql_string(raw_sql, app="auth")

# Streaming file-to-file pipeline
with open("dump.sql", "r", encoding="utf-8") as in_f, open("clean.sql", "w", encoding="utf-8") as out_f:
    stats = anonymize_sql_stream(in_f, out_f, app="counters")
```

## Models and wire helpers

`support_python.dates` provides wire datetime serialization and parsing, while `support_python.models`
provides kebab-case enum converters and metadata models for REST client libraries:

```python
from support_python import ApiInfo, ApiRoute, ServerStatus, WireEnum, format_datetime, parse_datetime

# Wire datetime helpers (UTC yyyy-MM-dd'T'HH:mm:ss'Z')
parsed_dt = parse_datetime("2026-09-18T14:00:00Z")
wire_date = format_datetime(parsed_dt)


# Base enum mapping to kebab-case wire strings
class TokenType(WireEnum):
    SESSION = "session"
    ONE_TIME_CODE = "one-time-code"


token = TokenType.from_wire("one-time-code")
assert token == TokenType.ONE_TIME_CODE

# Standard server metadata models
route = ApiRoute.from_wire({"method": "GET", "uri-pattern": "/api/status", "description": "Server health"})
info = ApiInfo.from_wire({"version": "1.0.0", "api-end-points": [route.to_wire()]})
status = ServerStatus.from_wire({"name": "service", "status": "OK", "uptime": "2 hours"})
```

## Installation and Releases

This project is distributed via Git and GitHub Releases.

### Install via Git

Install the package directly into a virtual environment:

```bash
python -m pip install git+https://github.com/gpellicciotta/support.python.git@v1.0.0
```

Or declare it in downstream `pyproject.toml` dependencies:

```toml
dependencies = [
    "support-python @ git+https://github.com/gpellicciotta/support.python.git@v1.0.0",
]
```

### GitHub Releases

When a release is published on GitHub, `.github/workflows/publish.yml` builds source and wheel packages,
attaching them as downloadable release assets.

## Version and dependencies

Project version is maintained in `pyproject.toml` under `[project].version`.
Dependencies are maintained in `pyproject.toml` under `[project].dependencies`.
