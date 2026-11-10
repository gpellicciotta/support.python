# Python Support Library

General-purpose Python support library and CLI, with as few third-party dependencies as possible.

Licensed under the [MIT License](LICENSE.md).

See also:
- [CHANGELOG](CHANGELOG.md)
- [Documentation index](docs/index.md)
- [Migrating to v2.0.0](docs/migration-v2.md)
- `PLAN.md`: task index (local plan store)

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
`python scripts/devops.py check` lints, tests, and builds through `.venv` in one step.
On GitHub pushes/PRs, the same artifacts are built (after lint and tests) by
[python-package.yml](.github/workflows/python-package.yml).

## Installing the command-line tools
Installing the `support-python` package installs all standalone command-line tools (`processes`, `agent-files`, `agent-digest`, `lint-markdown`, and `git-repository-backup`) together.
Upgrading from v1.x, where they ran as `support-python` subcommands or wrapper scripts? See [migration-v2.md](docs/migration-v2.md).

```bash
pipx install "git+https://github.com/gpellicciotta/support.python.git@v<version>"
uv tool install "git+https://github.com/gpellicciotta/support.python.git@v<version>"
pip install --user "git+https://github.com/gpellicciotta/support.python.git@v<version>"
python scripts/install-from-github-release.py <version> --global
```

From a local checkout, install into the active environment and invoke each command directly:

```bash
python -m pip install .
processes list --cwd .
agent-files list
agent-digest check guidelines
lint-markdown check [paths] [--offline]
git-repository-backup list --root ~/projects
```

## Repository maintenance scripts
`extract-release-notes.py`, `migrate-namespace.py`, and `reset-history.py` stay uninstalled under `scripts/`.
Each acts on the Git repository containing the current directory, so run it from a support-python checkout against any repository:

```bash
cd path/to/other-repo
python path/to/support.python/scripts/extract-release-notes.py 1.2.3
python path/to/support.python/scripts/migrate-namespace.py --old acme --new widgets rewrite
python path/to/support.python/scripts/reset-history.py backup ../backups
```

Each script imports `support_python` from the checkout's `src/` directory, or from an installed package.

## Shared CLI helpers, tabular output, and session storage

`support_python.cli` provides `ToolHarness`/`Action` (registered actions with handlers, fallback action, exit-code table, startup/exit banners, and `get_full_version`/`resolve_build_metadata` build-metadata version suffixes). `support_python.tables` provides tabular output formatting (`format_table`/`render_output`), and `support_python.tokens` provides persistent session token storage (`FileTokenStore`, `TokenStore`):

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

`support_python.CliLogger` (paired with `resolve_log_level`,
`normalize_log_level`, `format_invocation_start`, and `init_cli_logger`) provides unified guideline-compliant
logging for command-line tools:

```python
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
`support_python.devops` provides `stream_subprocess`, `run_step_command`, `resolve_executable`, `EXIT_COMMAND_NOT_FOUND`, `run_step`, `resolve_cloud_sql_proxy_bin`, `CloudSqlProxyManager`, `LocalDockerManager`,
`LocalMySqlManager`, `LocalServerManager`, `LocalMailManager`, and `LocalVerifier` for local developer
orchestration and deployment scripts. `stream_subprocess` merges child `stdout`/`stderr` line by line into a `CliLogger` with `stdin=DEVNULL`, logs the command and PID, runs an optional `on_line` callback, and terminates (then kills after 5s) the child on `KeyboardInterrupt`. `CloudSqlProxyManager` searches `PATH`, `repo_root`, and user or Cloud SDK `bin` directories, failing cleanly when Docker is missing:

```python
from support_python import (
    CliLogger,
    CloudSqlProxyManager,
    LocalDockerManager,
    LocalMySqlManager,
    LocalServerManager,
    run_step,
    run_step_command,
    stream_subprocess,
)

# Stream a subprocess line by line to a CliLogger with an optional raw-line callback
logger = CliLogger(log_path="build.log", origin="runner")
exit_code = stream_subprocess(["python", "-m", "pytest", "-q"], logger=logger, origin="pytest")

# Manage Docker Engine & Desktop
docker_mgr = LocalDockerManager()
if docker_mgr.get_status() != "running":
    docker_mgr.start_desktop()

# Manage Isolated MySQL Container & Snapshots
# Passwords have no defaults: pass them or define MYSQL_PASSWORD / MYSQL_ROOT_PASSWORD in the env file.
mysql_mgr = LocalMySqlManager(container_name="app-local-mysql", port=3306, mysql_env_file="mysql.env")
mysql_mgr.ensure_running()

# The Cloud SQL instance (project:region:instance) is mandatory.
# Discovers cloud-sql-proxy on PATH, repo_root, ~/bin, ~/.local/bin, or Cloud SDK bin before Docker fallback.
proxy_mgr = CloudSqlProxyManager("my-project:my-region:my-instance")

# Manage Local Application Server Process
server_mgr = LocalServerManager(port=8080)
server_mgr.start(background=True)
```

`support_python.devops.release` holds stdlib-only release helpers, also re-exported from `support_python.devops`.
`read_version`/`write_version` use the first of `pyproject.toml`, `gradle.properties`, and `package.json` that declares a version.
They keep line endings and write atomically. The CHANGELOG.md helpers follow the `-pre` and `[status]` heading convention:

```python
from pathlib import Path

from support_python.devops import (
    extract_release_notes,
    freeze_changelog,
    next_dev_version,
    open_dev_changelog,
    parse_github_repo,
    read_version,
    release_version,
    write_version,
)

root = Path(".")
changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
release = release_version(read_version(root))  # "1.2.3-pre" -> "1.2.3"
notes = extract_release_notes(changelog, release)  # ValueError when missing or empty
changelog = freeze_changelog(changelog, release, "released: 2026-11-09")  # "## v1.2.3 [released: 2026-11-09]"
changelog = open_dev_changelog(changelog, next_dev_version(release, "minor"))  # "## v1.3.0-pre" after the first "---"
write_version(root, next_dev_version(release, "minor"))
repo = parse_github_repo("git@github.com:owner/name.git")  # "owner/name"
```

`ReleasePipeline` runs the whole release from the repository root and returns 0 or 1.
It checks every precondition before any change: a clean tree, the main branch, an authenticated `gh`, and fresh tags.
It also requires no existing tag or GitHub release, and non-empty release notes.
It then runs the quality check and asks the user to type `release v<X>` unless `assume_yes` is set.
Next it freezes the `-pre` version, tags, pushes, and publishes a GitHub release with assets.
An optional `build` hook runs after the freeze commit and before tagging; `assets` is then resolved after it.
That way the assets carry the release version, and a failed build stops before anything is tagged or pushed.
Finally it reopens the next patch `-pre` version and pushes it.
`dry_run` logs every planned edit and command without prompting or changing anything.
Side-effecting commands go through `runner` (default `run_step_command`); read-only queries go through `query`:

```python
import sys
from pathlib import Path

from support_python import CliLogger
from support_python.devops import ReleasePipeline, run_step_command

root = Path(".")
pipeline = ReleasePipeline(
    root=root,
    logger=CliLogger(),
    quality_check=lambda: run_step_command([sys.executable, "-m", "pytest", "-q"], root) == 0,
    build=lambda: run_step_command([sys.executable, "-m", "build", "-o", "dist"], root) == 0,
    assets=lambda: sorted((root / "dist").glob("*")),
    dry_run="--dry-run" in sys.argv,
)
sys.exit(pipeline.run())
```

`confirm_typed(summary, phrase)` prints the summary lines and returns whether the user typed `phrase` exactly.

`DevopsCli` turns a `Project` into the standard `devops` command line on `ToolHarness`.
Its actions are `lint`, `format`, `test`, `build`, `check`, `clean`, `versions`, and `release`, plus `help` and `version`.
`check` runs lint, test, and build, stopping at the first failure.
`versions` exits 1 when the version file and the top `CHANGELOG.md` heading differ.
`release` runs `ReleasePipeline` with `check` as its quality check and `build` as its post-freeze build hook.
It attaches the outputs of that post-freeze build, never the `-pre` build from `check`.
`PythonProject` runs ruff, pytest, and build through `<root>/.venv` and exits 1 with a bootstrap hint when it is missing.
`GradleProject` runs `gradlew.bat` on Windows and `./gradlew` elsewhere, adding `--console=plain` (`gradle_options`):

| Action   | Default Gradle tasks                                | Keyword override |
|----------|-----------------------------------------------------|------------------|
| `lint`   | `spotlessCheck checkstyleMain checkstyleTest`       | `lint_tasks`     |
| `format` | `spotlessApply`                                     | `format_tasks`   |
| `test`   | `test`, plus `--tests ITEM` per selection item      | `test_tasks`     |
| `build`  | `build`                                             | `build_tasks`    |
| `check`  | `build`, once, since Gradle's build runs the checks | `check_tasks`    |
| `clean`  | `clean`                                             | `clean_tasks`    |

Test selection items starting with `-` pass to Gradle unchanged.
It reads the version from `gradle.properties` and releases `build/libs/*.jar` and `*/build/libs/*.jar`.
With `release_task`, `release` asks for the typed confirmation, then runs that task with `release_args` instead of `ReleasePipeline`.
`release --dry-run` runs the task with Gradle's own `--dry-run` and no prompt.
For example, `GradleProject(REPO_ROOT, release_task="doFullRelease", release_args=["-PreleaseConfirmed=yes"])`.
`NodeProject` runs npm scripts, resolving `npm` through `resolve_executable` so Windows finds `npm.cmd`:

| Action   | npm commands                                                            |
|----------|-------------------------------------------------------------------------|
| `lint`   | `npm run lint`                                                          |
| `format` | `npm run format`                                                        |
| `test`   | `npm test`, plus `-- ITEM...` with selection items                      |
| `build`  | `npm run build` when defined, then `npm pack --pack-destination dist`   |
| `check`  | lint, test, then build                                                  |
| `clean`  | removes `dist/`                                                         |

A script missing from `package.json` fails with an error naming it.
`build` clears `dist/` first; the version lives in `package.json`, and `release` attaches `dist/*.tgz`.
Commands go through an injectable `runner` (default `run_step_command`), and `add_action` adds project-specific actions.
A consumer's devops script stays as thin as this repository's own [devops.py](scripts/devops.py):

```python
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from support_python.devops import DevopsCli, PythonProject  # noqa: E402

if __name__ == "__main__":
    sys.exit(DevopsCli(PythonProject(REPO_ROOT)).run())
```

`set_deploy(steps, verify=None, require_ci=True, environment="production")` adds a `deploy` action.
Each `DeployStep` has a `name` and exactly one of `command` (run through the project runner) or `action`.
An `action` and the `verify` callback receive a `DeployContext` with `project`, `version`, `logger`, and `dry_run`.
`deploy [--dry-run] [--yes] [--skip-ci-check]` checks these preconditions before running anything:
- The working tree is clean, including untracked files.
- The version has no `-pre` suffix.
- Tag `v<version>` exists on `origin` and points at HEAD.
- `gh run list --commit <HEAD>` shows a successful completed run and no failed one (skip with `--skip-ci-check`).

It then asks for the typed confirmation `deploy v<version>` unless `--yes` is given.
It runs the steps in order, stops at the first failure, then runs `verify`; any failure exits 1.
`--dry-run` checks the preconditions and logs the plan without prompting or running a step.
Without `set_deploy`, `deploy` is neither listed nor accepted:

```python
cli = DevopsCli(PythonProject(REPO_ROOT))
cli.set_deploy(
    [DeployStep("push image", command=["docker", "push", IMAGE]), DeployStep("migrate", action=run_migrations)],
    verify=check_live_version,
)
sys.exit(cli.run())
```

`add_services(...)` adds opt-in action groups backed by the `support_python.devops.services` managers.
A group appears only when its manager is passed; its first argument selects the sub-action:

| Group    | Manager keywords | Sub-actions (default first)                                     |
| :------- | :--------------- | :-------------------------------------------------------------- |
| `docker` | `docker`         | `status`, `start`                                               |
| `db`     | `mysql`, `proxy` | `status`, `start`, `stop`, `snapshot`, `load-snapshot`, `proxy` |
| `server` | `server`         | `status`, `start`, `stop`                                       |
| `mail`   | `mail`           | `test-emails`                                                   |
| `client` | `verifier`       | `verify`, `verify-deployment`                                   |

Options follow the auth, counters.server, and todos.server scripts they replace:
- `db snapshot`: `--source`, `--input-file`, `--output-file`, `--load-target`, `--confirm-production-access`, `--custom-password`.
- `db load-snapshot`: a `PATH` right after the sub-action or `--snapshot-path`, plus `--target`.
- `db proxy`: `--address`, `--port`, `--instance`, and `--credentials-file`, overriding the manager's settings.
- `server start`: `--background`/`-d`, `--build`/`--force-build`, `--memory-db`, `--verify`, and `--testdb`.
- `mail test-emails`: a `RECIPIENT` or `--to`, plus `--app-name`, `--env-file`, and `--build`/`--force-build`.
- `client verify-deployment`: `--url`, `--expected-version`, `--attempts`, `--retry-delay`, and `--timeout`.

- `db proxy` needs `proxy`; the other `db` sub-actions need `mysql`.
- `db_targets` (default `("local", "testdb")`) sets the `--load-target` and `--target` choices.
- Each target is `local`, `testdb` (loads into `<db_name>_test`), or a `<name>_test` alias loading into that database.
- Any other `db_targets` entry raises `ValueError`.
- `server start` starts MySQL first unless `--memory-db` or `--testdb` is given, or no `mysql` manager was passed.
- `testdb_env_file` enables `server start --testdb`, which runs the server with that environment file.
- `server start --verify` and `client verify` call `LocalVerifier.run_all_checks()`; override it for app checks.
- `service_url` sets the default `--url`; without it, `client verify-deployment` requires `--url`.
- An unknown sub-action, a misplaced positional argument, or a missing snapshot path, recipient, or URL exits 2.

```python
cli = DevopsCli(GradleProject(REPO_ROOT))
server = LocalServerManager(port=8080, repo_root=REPO_ROOT, app_name="Todos")
cli.add_services(
    docker=LocalDockerManager(),
    mysql=LocalMySqlManager(container_name="todos-mysql", repo_root=REPO_ROOT),
    proxy=CloudSqlProxyManager(instance="project:region:instance"),
    server=server,
    mail=LocalMailManager(server_manager=server),
    verifier=LocalVerifier(port=8080),
    db_targets=("local", "testdb", "todos_test"),
    service_url="https://todos.example.com",
    testdb_env_file=REPO_ROOT / "config" / "todos-testdb-devserver.env",
)
sys.exit(cli.run())  # e.g. `devops db start`, `devops server start --memory-db`
```

## View Capture Engine and Static Server

`support_python.capture` provides browser screenshot automation (`ViewCaptureEngine`) and visual UI tour
orchestration (`run_tour`, `run_capture_cli`). `run_capture_cli` runs a `ToolHarness` CLI
(`build_capture_harness`) with `capture` (the default action), `tour`, `list`, `version`, and `help` actions.
Embedded static web serving is provided by
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

When a release is published on GitHub, [publish.yml](.github/workflows/publish.yml) builds source and wheel packages,
attaching them as downloadable release assets.

## Version and dependencies

Project version is maintained in `pyproject.toml` under `[project].version`.
Dependencies are maintained in `pyproject.toml` under `[project].dependencies`.

## Git repository helpers
The package exports Git helpers from [git.py](src/support_python/git.py), also available through `support_python.git`.
Git must be installed and available on `PATH`; no Python dependencies are required.

```python
from support_python import get_repo_root, has_remote, is_git_clean

root = get_repo_root(".")
clean = is_git_clean(".")
if clean is None:
    print("Repository status could not be queried")
elif clean:
    print("Working tree is clean")
else:
    print("Working tree has changes")

remote = has_remote(".", "origin")  # True: configured; False: absent; None: query failed.
```

All repository queries return `None` on execution failure, including missing Git, timeouts, and invalid repositories.
`is_git_clean`, `has_remote`, and `branch_exists` return `False` only for confirmed negative results.
Use `result is None` to distinguish failures from negative results.
This intentionally differs from plan's original clean and remote helpers, which returned `False` on errors.
`get_head_commit` also returns `None` before the first commit.
`get_current_branch` returns `"(detached)"` for detached HEAD.
An unborn branch has a symbolic name but does not yet exist as a branch ref.

`get_working_tree_status` returns dictionaries containing `status`, `path`, and optional `original_path` for renames or copies.
`list_worktrees` returns dictionaries using Git's porcelain keys, including `worktree`, `HEAD`, `branch`, and optional flags.
Flags such as `detached` have empty string values.
Both queries use NUL-delimited output to preserve filenames containing whitespace, quotes, or newlines.
`parse_status_porcelain` and `parse_worktree_porcelain` also accept newline-delimited output for simple fixtures.
Newline status parsing does not decode Git's quoted escape sequences; use NUL-delimited output for arbitrary filenames.

`run_git_command(cwd, *args)` returns `subprocess.CompletedProcess[str]` with UTF-8 stdout and stderr.
It raises `CalledProcessError` for disallowed exit codes, `TimeoutExpired` for timeouts, and `OSError` for execution failures.
The default timeout is 10 seconds; `allowed_returncodes`, `env`, and `input_data` customize execution.
Defaults disable optional locks, lazy fetching, and terminal prompts; caller environment overrides take precedence.
`no_optional_locks=False` omits the command flag; override `GIT_OPTIONAL_LOCKS` separately if optional locks are needed.
The runner accepts arbitrary Git commands, including mutations; repository query helpers only inspect local state.

## Locking
The package exports locks from [locking.py](src/support_python/locking.py), also available through `support_python.locking`.
The core has no Python dependencies.

```python
from support_python import LockTimeoutError, create_lock

lock = create_lock("file", path=".app/.app.lock", timeout=5.0)
try:
    with lock:
        ...  # Critical section; nested `with` blocks in one thread are re-entrant.
except LockTimeoutError as error:
    print(error)  # Includes holder diagnostics when the holder is in this process.
```

- `FileLock` uses `msvcrt` on Windows and `fcntl` elsewhere; the OS frees it when a process dies.
- `NullLock` always succeeds; use it for tests or disabled locking.
- `RedisLock` provides distributed locking backed by Redis using `SET NX PX` and an atomic Lua release script. It requires the `redis` optional extra (`pip install support-python[redis]`).
- `MySQLLock` provides distributed server-wide advisory locking backed by MySQL using `GET_LOCK` and `RELEASE_LOCK`. It requires the `mysql` optional extra (`pip install support-python[mysql]`).
- `create_lock(backend, key, path, timeout, poll_interval, max_jitter, ttl)` maps `null`/`none` to `NullLock`.
  `file`, `local`, or an empty value select `FileLock` and require `path`.
  `redis://` and `rediss://` select `RedisLock` and require `key`.
  `mysql://`, `mysql+pymysql://`, and `jdbc:mysql://` select `MySQLLock` and require `key`.
  Unsupported schemes raise `ValueError`.
- Timeouts and TTLs are floats in seconds.

## Process hierarchy and safe termination
The package exports process helpers from [processes.py](src/support_python/processes.py) and the `processes` CLI from [tools/processes.py](src/support_python/tools/processes.py) (see [processes.md](docs/tools/processes.md)).
All helpers use only the Python standard library and `ctypes`.

```python
import os
from support_python.processes import (
    get_process_cwd,
    get_process_descendants,
    get_process_hierarchy,
    get_process_start_time,
    is_process_alive,
    list_processes,
    safe_kill,
    terminate_process_tree,
)

pid = os.getpid()
ancestors = get_process_hierarchy(pid)
descendants = get_process_descendants(pid)
cwd = get_process_cwd(pid)
started = get_process_start_time(pid)
alive = is_process_alive(pid, expected_start=started, slack_seconds=2.0)
matching = list_processes(cwd=cwd, descendants_of=pid)
safe_kill([pid])  # Skips the current process and its ancestors with a warning.
```

```bash
processes list --cwd . --format json
processes list --open-path locked.txt --started-after 2026-11-07T00:00:00
processes kill 1234 5678 --force
processes kill 1234 5678 --dry-run
processes list --descendants-of 1234
```

- `get_process_hierarchy(start_pid)` returns `start_pid` and all ancestor PIDs, failing closed with `OSError` when inspection fails.
- `get_process_descendants(start_pid)` returns `start_pid` and all child and descendant PIDs.
- `get_process_cwd(pid)` and `find_pids_with_open_path(path)` inspect process working directories and open files across Windows, Linux, and macOS.
- `list_processes(...)` and `filter_processes(...)` filter `ProcessInfo` records by `--cwd`, `--open-path`, `--started-before`, `--started-after`, `--ancestors-of`, and `--descendants-of`.
- `windows_parent_map()` enumerates running Windows processes via `CreateToolhelp32Snapshot` without spawning a shell.
- `get_process_start_time(pid)` returns a naive local `datetime`, or `None` if the process is absent.
- `is_process_alive(pid, expected_start=None, slack_seconds=2.0)` checks liveness and guards against recycled PIDs.
- `terminate_process(pid, force=False)` signals one positive PID directly; callers must enforce ancestor protection first.
- `terminate_process_tree(pid)` terminates a process and its child tree, returning `False` on invalid PIDs or failures.
- `safe_kill(pids, logger=None, force=False)` skips the current process and ancestors with a warning and returns `bool`.

## Atomic text file helpers
The package exports atomic file helpers from [files.py](src/support_python/files.py), also available through `support_python.files`.
All helpers use only the Python standard library.

```python
from pathlib import Path
from support_python import atomic_replace, atomic_write_text, read_text_retrying

path = Path("state.txt")
atomic_write_text(path, "consistent text\n")
content = read_text_retrying(path, errors="strict")
```

- `atomic_write_text(path, content, newline=None)` writes UTF-8 text via a temporary sibling file so readers never see partial content.
- `atomic_write_text` preserves existing POSIX permission bits, omits the target filename from the temporary name, and removes failed temporaries.
- `atomic_replace(src, dst, max_retries=15, base_delay=0.01)` replaces `dst` with `src`, retrying transient `PermissionError` and Windows error `5` or `32`.
- `read_text_retrying(path, max_retries=10, base_delay=0.005, errors="replace")` reads UTF-8 text while retrying transient `PermissionError` locks during concurrent renames.

## Markdown table helpers
The package exports Markdown table helpers from [tables.py](src/support_python/markdown/tables.py), also available through `support_python.markdown`.
All helpers use only the Python standard library and preserve `support_python.tables.format_table`.

```python
from support_python import (
    check_table_alignment,
    format_markdown_table,
    format_markdown_table_block,
    strip_ansi,
    visible_width,
)

table = format_markdown_table(["Name", "Score"], [["\x1b[32mAlice\x1b[0m", "100"]], alignments=["left", "right"])
issues = check_table_alignment(table)
```

- `strip_ansi(text)` removes ANSI CSI escape sequences, and `visible_width(text)` returns the stripped character count.
- `find_delimiter_pipes(line)` finds unescaped pipe indices outside backtick code spans, and `split_table_row(line)` returns trimmed cells.
- `is_table_delimiter_row(line)` validates GitHub Flavored Markdown separator rows such as `:---`, `:---:`, and `---:`.
- `format_markdown_table(headers, rows, alignments=None)` formats aligned GFM tables using visible cell widths.
- `format_markdown_table_block(table_lines)` reformats raw table lines in place while preserving leading blockquote prefixes.
- `check_table_alignment(content)` returns `TableAlignmentIssue` entries for any table rows with misaligned delimiter pipes.

## Markdown linter
`support_python.markdown` ([lint.py](src/support_python/markdown/lint.py), [registry.py](src/support_python/markdown/registry.py), [rules.py](src/support_python/markdown/rules.py), [profiles.py](src/support_python/markdown/profiles.py)) provides `MarkdownLinter`, `LintIssue`, `RuleRegistry`, `LintProfile`, and `load_profile` (also re-exported from `support_python`), with the `lint-markdown` CLI in [lint_markdown.py](src/support_python/tools/lint_markdown.py) reading `.lint-markdown.json` (or legacy `.markdown-lint.json` with a warning; see [lint-markdown.md](docs/tools/lint-markdown.md)):
```bash
lint-markdown check [paths...] [--format text|json] [--offline] [--profile PROFILE] [--config PATH] [--plugin ENTRY]... [--rules MD001,MD017] [--exclude GLOB]
lint-markdown fix [paths...] [--dry-run] [--offline] [--profile PROFILE] [--config PATH] [--plugin ENTRY]... [--rules MD001,MD017] [--exclude GLOB]
lint-markdown rules [--format text|json] [--profile PROFILE] [--config PATH] [--plugin ENTRY]...
```

Extra rules load from plugin files or modules listed under the config `plugins` key or passed with `--plugin`.
Each plugin defines `register(registry)`; `rules` lists every rule with its source (see [lint-markdown.md](docs/tools/lint-markdown.md#rule-plugins)).

## Agent files sync
[agent_files.py](src/support_python/tools/agent_files.py) and [agent_files_config.py](src/support_python/tools/agent_files_config.py) install an existing digest and skills directory into configured AI coding tools (`ToolRegistry`, `AgentFilesConfig`, `load_agent_files_config`), exposed on the CLI as `agent-files`.
It reads `./agent-digest.md` and `./agent-skills` by default and never regenerates them; run `agent-digest generate` first, or `sync` and `check` exit 1.
Settings load from `.agent-files.json` in the repository root (falling back to `agent-files.json` with a warning, or `--config PATH`) with CLI flag overrides; see [agent-files.md](docs/tools/agent-files.md) for the full JSON schema and tool registry documentation:
```bash
agent-files list [--format text|json] [--config PATH]
agent-files sync [TOOL...] [--config PATH] [--repo-root PATH] [--digest PATH] [--skills-dir PATH] [--marker NAME] [--marker-begin TEXT] [--marker-end TEXT] [--manifest-source NAME] [--legacy-skill NAME] [--dry-run] [--no-prune]
agent-files check [TOOL...] [--format text|json] [--config PATH] [--repo-root PATH] [--digest PATH] [--skills-dir PATH] [--marker NAME] [--marker-begin TEXT] [--marker-end TEXT] [--manifest-source NAME] [--legacy-skill NAME]
agent-files review [TOOL...] [--config PATH] [--repo-root PATH] [--timeout SECONDS]
```

## Agent digest generator
[agent_digest.py](src/support_python/tools/agent_digest.py) builds a Markdown digest and `<name>/SKILL.md` skills from `<PATH>...` inputs and validates budgets (see [agent-digest.md](docs/tools/agent-digest.md)):
```bash
agent-digest generate <PATH>... [--digest PATH] [--skills-dir PATH] [--link-base URL] [--max-words N] [--max-bytes N]
agent-digest check <PATH>... [--digest PATH] [--skills-dir PATH] [--link-base URL] [--max-words N] [--max-bytes N] [--skill-index FILE]
```

## Git repository backup
[git_repository_backup.py](src/support_python/tools/git_repository_backup.py) backs up discovered Git repositories to bare mirror repositories and AES-256 encrypted 7-Zip bundle archives, exposed on the CLI as `git-repository-backup`.
Settings load from `~/.config/git-repository-backup/config.json` (falling back to `~/.config/backup-git-repos/config.json` with a warning, or `--config PATH`); see [git-repository-backup.md](docs/tools/git-repository-backup.md) for the full JSON schema and action reference:
```bash
git-repository-backup list [--root PATH] [--format text|json] [--config PATH]
git-repository-backup backup [--root PATH] [--mirror-dir PATH] [--archive-dir PATH] [--dry-run] [--config PATH]
git-repository-backup restore (--source PATH | --name NAME) --target DIR [--config PATH]
git-repository-backup set-password --archive-dir PATH --password-keyring NAME [--config PATH]
```

## Duration and time formatting helpers
The package exports duration and timestamp helpers from [durations.py](src/support_python/durations.py), also available through `support_python.durations`.
All helpers use only the Python standard library and preserve `support_python.dates.format_datetime`.

```python
from support_python import (
    format_duration,
    format_epoch,
    format_past_epoch,
    format_short_duration,
    parse_date_or_datetime,
    parse_duration_to_seconds,
    parse_iso8601,
)

seconds = parse_duration_to_seconds("1h 02m 05s")  # 3725.0
label = format_duration(seconds)  # "1h 02m 05s"
short = format_short_duration(seconds)  # "1h 2m"
ts = parse_iso8601("2026-09-11T10:00:00Z")
dt = parse_date_or_datetime("2026-09-11 10:00:00")
future = format_epoch(ts + seconds, now_ts=ts)
past = format_past_epoch(ts, now_ts=ts + seconds)
```

- `parse_iso8601(text)` parses an ISO 8601 timestamp (including trailing `Z`) into a POSIX float timestamp, or `None` on invalid input.
- `parse_date_or_datetime(text)` parses `YYYY-MM-DD`, `YYYY-MM-DD[T ]HH:MM[:SS]`, or a `YYYY-MM-DD` prefix into a naive `datetime`, or `None`.
- `parse_duration_to_seconds(dur_str, default_unit="s")` parses single or compound units (`d`, `h`, `m`, `s`, `ms`) and bare numbers into seconds, returning `None` for invalid or negative input.
- `format_duration(seconds)` formats durations as `<sec.f>s`, `<m>m <ss>s`, `<h>h <mm>m <ss>s`, or `<d>d <hh>h` (clamping negatives to `0.0s`).
- `format_short_duration(seconds)` formats durations as `<secs>s` under 2 minutes, `<m>m` under 1 hour, `<h>h <m>m` under 1 day, or `<d>d <h>h`.
- `format_epoch(ts, now_ts=None)` formats a target timestamp as `YYYY-MM-DD HH:MM:SS (in <duration>)`.
- `format_past_epoch(ts, now_ts=None)` formats a past timestamp as `YYYY-MM-DD HH:MM (<short_duration> ago)`.

## Task rate limiter
The package exports `TaskRateLimiter` from [ratelimit.py](src/support_python/ratelimit.py), also available through `support_python.ratelimit`.
It uses only the Python standard library and pairs with [durations.py](src/support_python/durations.py) for wait-duration formatting.

```python
from support_python import TaskRateLimiter, format_duration

limiter = TaskRateLimiter(max_tasks_per_hour=2, window_seconds=3600.0)
if limiter.can_dispatch():
    limiter.record_dispatch()
else:
    wait_seconds = limiter.get_wait_duration()
    print(f"Rate limit reached; retry in {format_duration(wait_seconds)}")
```

- `TaskRateLimiter(max_tasks_per_hour=None, window_seconds=3600.0)` tracks dispatch timestamps in a sliding window.
- `is_enabled` is `True` only when `max_tasks_per_hour` is set and greater than `0`.
- `prune(now=None)` removes recorded timestamps at or before `now - window_seconds`.
- `can_dispatch(now=None)` prunes expired timestamps and returns `True` when disabled or below capacity.
- `get_wait_duration(now=None)` returns `0.0` when dispatch is allowed, or `max(1.0, oldest + window_seconds - now)` when blocked.
- `record_dispatch(now=None)` appends a dispatch timestamp when enabled.
