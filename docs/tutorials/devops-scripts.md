# DevOps Scripts

`support_python.devops` provides the building blocks for local developer orchestration and deployment scripts.
A consumer's devops entry script stays a few lines long, while lint, test, build, release, deploy, and local service actions come from the library.

Modules:
- [steps.py](../../src/support_python/devops/steps.py): subprocess streaming and step runners.
- [services.py](../../src/support_python/devops/services.py): Docker, MySQL, Cloud SQL proxy, server, mail, and verification managers.
- [release.py](../../src/support_python/devops/release.py): version-file and `CHANGELOG.md` helpers, and `ReleasePipeline`.
- [projects.py](../../src/support_python/devops/projects.py): `PythonProject`, `GradleProject`, and `NodeProject` adapters.
- [cli.py](../../src/support_python/devops/cli.py), [deploy.py](../../src/support_python/devops/deploy.py), and [service_actions.py](../../src/support_python/devops/service_actions.py): `DevopsCli`, its `deploy` action, and its service action groups.

Every devops symbol below is importable from `support_python.devops`; the step runners and service managers are also re-exported from `support_python`.

## Subprocess steps and local service managers
- `stream_subprocess` merges child `stdout`/`stderr` line by line into a `CliLogger`, with `stdin=DEVNULL`.
  It logs the command and PID, runs an optional `on_line` callback, and terminates (then kills after 5s) the child on `KeyboardInterrupt`.
- `run_step_command`, `run_step`, `resolve_executable`, and `EXIT_COMMAND_NOT_FOUND` run build steps and resolve executables.
- `resolve_cloud_sql_proxy_bin` searches `PATH`, `repo_root`, and user or Cloud SDK `bin` directories for `cloud-sql-proxy`.
- `CloudSqlProxyManager` uses that search, falls back to Docker, and fails cleanly when Docker is missing.
- `LocalDockerManager`, `LocalMySqlManager`, `LocalServerManager`, `LocalMailManager`, and `LocalVerifier` manage local developer services.
- Constructor parameters override the support.java conventions; each default keeps the current behavior.
  - `LocalServerManager`: `environment_file_option`, `config_file_option`, `log_file_option` (`None` omits each), `mail_backend_args`, `memory_db_args`, `start_args`, `static_dir_env_var`.
  - `LocalMailManager`: `test_mail_args`; it reuses the server manager's file options.
  - `LocalVerifier`: `health_endpoint`, `running_status`, `default_assets`; local and remote checks share them.
  - `LocalMySqlManager`: `prod_env_file_name` and `test_env_file_name` templates, with `{{app}}` and `{{db-name}}` or `{{db_name}}`.

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

## Release helpers
`support_python.devops.release` holds stdlib-only release helpers, also re-exported from `support_python.devops`.
`read_version`/`write_version` use the first of `pyproject.toml`, `gradle.properties`, and `package.json` that declares a version.
They keep line endings and write atomically.
The `CHANGELOG.md` helpers follow the `-pre` and `[status]` heading convention:

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

## Release pipeline
`ReleasePipeline` runs the whole release from the repository root and returns 0 or 1:
- It checks every precondition before any change: a clean tree, the main branch, an authenticated `gh`, and fresh tags.
- It also requires no existing tag or GitHub release, and non-empty release notes.
- It then runs the quality check and asks the user to type `release v{{version}}` unless `assume_yes` is set.
- Next it freezes the `-pre` version, tags, pushes, and publishes a GitHub release with assets.
- An optional `build` hook runs after the freeze commit and before tagging; `assets` is then resolved after it.
- That way the assets carry the release version, and a failed build stops before anything is tagged or pushed.
- Finally it reopens the next patch `-pre` version and pushes it.
- `dry_run` logs every planned edit and command without prompting or changing anything.
- Side-effecting commands go through `runner` (default `run_step_command`); read-only queries go through `query`.

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

## DevopsCli and project adapters
`DevopsCli` turns a `Project` into the standard `devops` command line on `ToolHarness`.
Its actions are:
- `lint`, `format`, `test` (with `--slow` for the slow suite), `build`, and `clean`.
- `check`, which runs lint, fast and slow tests, and build, stopping at the first failure.
- `versions`, which exits 1 when the version file and the top `CHANGELOG.md` heading differ.
- `versions VERSION [--dry-run]`, which sets the manifest and active changelog heading to `MAJOR.MINOR.PATCH-pre`.
  `VERSION` accepts an optional `-pre`; malformed versions and finalized headings are refused before writing.
  All three adapters share `Project.set_version(version, dry_run=False)`, returning whether the update succeeds.
- `release`, which runs `ReleasePipeline` with `check` as its quality check and `build` as its post-freeze build hook.
  It attaches the outputs of that post-freeze build, never the `-pre` build from `check`.
- `help` and `version`, from `ToolHarness`.

Without supported manifests, `version`, `versions`, and `release` use the first `## v` heading in [CHANGELOG.md](../../CHANGELOG.md).
`versions VERSION` updates only that heading; release freezes it and opens the next development heading.
Supported manifests take precedence; manifests without declared versions still fail rather than using the changelog.

Commands go through an injectable `runner` (default `run_step_command`), and `add_action` adds project-specific actions.
Each adapter's `action_summaries()` replaces the generic help summaries, and `test_selection_example` sets the `test` help example.
`GradleProject` names the Gradle tasks of each action in its help, and its `release_task` in the `release` summary.
`DevopsCli` reads both when it is built, so set adapter attributes such as task lists first.
A consumer's devops script stays as thin as this repository's own [devops.py](../../scripts/devops.py):

```python
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from support_python.devops import DevopsCli, PythonProject  # noqa: E402

if __name__ == "__main__":
    sys.exit(DevopsCli(PythonProject(REPO_ROOT)).run())
```

### PythonProject
`PythonProject` runs ruff, pytest, and build through `{{project-root}}/.venv` and exits 1 with a bootstrap hint when it is missing.
`test --slow` runs `pytest -m slow --timeout=120` through the venv.

### GradleProject
`GradleProject` runs `gradlew.bat` on Windows and `./gradlew` elsewhere, adding `--console=plain` (`gradle_options`):

| Action        | Default Gradle tasks                                | Keyword override  |
| :------------ | :-------------------------------------------------- | :---------------- |
| `lint`        | `spotlessCheck checkstyleMain checkstyleTest`       | `lint_tasks`      |
| `format`      | `spotlessApply`                                     | `format_tasks`    |
| `test`        | `test`, plus `--tests ITEM` per selection item      | `test_tasks`      |
| `test --slow` | `slowTest`, plus `--tests ITEM` per selection item  | `slow_test_tasks` |
| `build`       | `build`                                             | `build_tasks`     |
| `check`       | `build`, once, since Gradle's build runs the checks | `check_tasks`     |
| `clean`       | `clean`                                             | `clean_tasks`     |

Test selection items starting with `-` pass to Gradle unchanged.
It reads the version from `gradle.properties` and releases `build/libs/*.jar` and `*/build/libs/*.jar`.
With `release_task`, `release` asks for the typed confirmation, then runs that task with `release_args` instead of `ReleasePipeline`.
`release --dry-run` runs the task with Gradle's own `--dry-run` and no prompt.
`release --skip-checks` has no effect with a `release_task` and logs a warning.
For example, `GradleProject(REPO_ROOT, release_task="doFullRelease", release_args=["-PreleaseConfirmed=yes"])`.

### NodeProject
`NodeProject` runs npm scripts, resolving `npm` through `resolve_executable` so Windows finds `npm.cmd`:

| Action        | npm commands                                                                |
| :------------ | :-------------------------------------------------------------------------- |
| `lint`        | `npm run lint`                                                              |
| `format`      | `npm run format`                                                            |
| `test`        | `npm test`, plus `-- ITEM...` with selection items                          |
| `test --slow` | `npm run test:slow`, plus `-- ITEM...` with selection items (skips if none) |
| `build`       | `npm run build` when defined, then `npm pack --pack-destination dist`       |
| `check`       | lint, fast and slow tests, then build                                       |
| `clean`       | removes `dist/`                                                             |

A script missing from `package.json` fails with an error naming it.
`build` clears `dist/` first; the version lives in `package.json`, and `release` attaches `dist/*.tgz`.

## Deploy action
`set_deploy(steps, verify=None, require_ci=True, environment="production")` adds a `deploy` action.
Each `DeployStep` has a `name` and exactly one of `command` (run through the project runner) or `action`.
An `action` and the `verify` callback receive a `DeployContext` with `project`, `version`, `logger`, and `dry_run`.
`deploy [--dry-run] [--yes] [--skip-ci-check]` checks these preconditions before running anything:
- The working tree is clean, including untracked files.
- The version has no `-pre` suffix.
- Tag `v{{version}}` exists on `origin` and points at HEAD.
- `gh run list --commit {{head-commit}}` shows a successful completed run and no failed one (skip with `--skip-ci-check`).

It then asks for the typed confirmation `deploy v{{version}}` unless `--yes` is given.
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

## Service action groups
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
- `db snapshot`: `--source`, `--input-file`, `--output-file`, `--load-target`, `--confirm-production-access`.
- `db load-snapshot`: a `PATH` right after the sub-action or `--snapshot-path`, plus `--target`.
- `db proxy`: `--address`, `--port`, `--instance`, and `--credentials-file`, overriding the manager's settings.
- `server start`: `--background`/`-d`, `--build`/`--force-build`, `--memory-db`, `--verify`, and `--testdb`.
- `mail test-emails`: a `RECIPIENT` or `--to`, plus `--app-name`, `--env-file`, and `--build`/`--force-build`.
- `client verify-deployment`: `--url`, `--expected-version`, `--attempts`, `--retry-delay`, and `--timeout`.

Behavior rules:
- `db proxy` needs `proxy`; the other `db` sub-actions need `mysql`.
- `db_targets` (default `("local", "testdb")`) sets the `--load-target` and `--target` choices.
- Each target is `local`, `testdb` (loads into `{{db-name}}_test`), or a `{{name}}_test` alias loading into that database.
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
