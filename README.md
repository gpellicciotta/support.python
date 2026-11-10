# Python Support Library

General-purpose Python support library and standalone command-line tools, with as few third-party dependencies as possible.

Licensed under the [MIT License](LICENSE.md).

See also:
- [CHANGELOG](CHANGELOG.md)
- [Documentation index](docs/index.md)
- [Migrating to v2.0.0](docs/migration-v2.md)

## Bootstrap
```bash
# Cross-platform (Windows/Linux/macOS): creates a venv, installs editable + dev extras, lints, tests, and builds
python scripts/bootstrap-dev-environment.py
```

See [devops.md](docs/devops.md) for the full development and release workflow, including the repository maintenance scripts.

## Build
```bash
python -m pip install --upgrade build
python -m build
```

This creates both source (`dist/*.tar.gz`) and binary wheel (`dist/*.whl`) packages.
`python scripts/devops.py check` lints, tests, and builds through `.venv` in one step.
On GitHub pushes and pull requests, [python-package.yml](.github/workflows/python-package.yml) builds the same artifacts after lint and tests.

## Install
This project is distributed via Git and GitHub Releases; replace `<version>` with a released version such as `2.0.0`.

Install the command-line tools globally; `pipx` and `uv tool` give them an isolated environment:

```bash
pipx install "git+https://github.com/gpellicciotta/support.python.git@v<version>"
uv tool install "git+https://github.com/gpellicciotta/support.python.git@v<version>"
pip install --user "git+https://github.com/gpellicciotta/support.python.git@v<version>"
python scripts/install-from-github-release.py <version> --global
```

Install the library into a virtual environment, or declare it in a downstream `pyproject.toml`:

```bash
python -m pip install "git+https://github.com/gpellicciotta/support.python.git@v<version>"
```

```toml
dependencies = [
    "support-python @ git+https://github.com/gpellicciotta/support.python.git@v<version>",
]
```

The `redis` and `mysql` extras add the `RedisLock` and `MySQLLock` backends, for example `support-python[redis]`.
From a local checkout, `python -m pip install .` installs the library and every command-line tool into the active environment.
When a release is published on GitHub, [publish.yml](.github/workflows/publish.yml) attaches its source and wheel packages as release assets.
The version lives in `pyproject.toml` under `[project].version`, and dependencies under `[project].dependencies`.

## Command-line tools
Installing the package installs five standalone console scripts:

| Tool                    | Purpose                                                               | Documentation                                                   |
| :---------------------- | :-------------------------------------------------------------------- | :-------------------------------------------------------------- |
| `processes`             | List processes by filter and kill them safely                         | [processes.md](docs/tools/processes.md)                         |
| `agent-digest`          | Generate an agent instruction digest and skills from Markdown files   | [agent-digest.md](docs/tools/agent-digest.md)                   |
| `agent-files`           | Install or update the digest and skills in AI coding tools            | [agent-files.md](docs/tools/agent-files.md)                     |
| `lint-markdown`         | Check and fix Markdown style and links                                | [lint-markdown.md](docs/tools/lint-markdown.md)                 |
| `git-repository-backup` | Back up Git repositories to bare mirrors and encrypted 7-Zip archives | [git-repository-backup.md](docs/tools/git-repository-backup.md) |

```bash
processes list --cwd .
agent-digest check guidelines
agent-files list
lint-markdown check [paths] [--offline]
git-repository-backup list --root ~/projects
```

Every tool supports `help`, `version`, `-h`/`--help`, `--version`, and `--verbose`.
Upgrading from `v1.x`, where they ran as `support-python` subcommands or wrapper scripts? See [migration-v2.md](docs/migration-v2.md).

## Library
Most library symbols are re-exported from the `support_python` package root.
Each tutorial shows a package group's main uses and import paths:

| Tutorial                                                                     | Modules                                       | Main uses                                                                    |
| :--------------------------------------------------------------------------- | :-------------------------------------------- | :--------------------------------------------------------------------------- |
| [CLI harness and logging](docs/tutorials/cli-harness-and-logging.md)         | `cli`, `logging`, `tables`, `tokens`          | Action-oriented CLIs, guideline-compliant logging, table output, token store |
| [Script utilities](docs/tutorials/script-utilities.md)                       | `terminal`, `version`, `net`, `env`, `crypto` | UTF-8 console, project version, port checks, env files, password hashing     |
| [REST clients](docs/tutorials/rest-clients.md)                               | `net`, `errors`, `dates`, `models`            | HTTP transport, error mapping, wire datetimes and models                     |
| [DevOps scripts](docs/tutorials/devops-scripts.md)                           | `devops`                                      | Thin devops entry scripts: lint, test, build, release, deploy, services      |
| [Git helpers](docs/tutorials/git-helpers.md)                                 | `git`                                         | Tri-state repository queries and a Git command runner                        |
| [Files and locking](docs/tutorials/files-and-locking.md)                     | `files`, `locking`                            | Atomic text writes and file, Redis, and MySQL locks                          |
| [Process management](docs/tutorials/process-management.md)                   | `processes`                                   | Process trees, PID-reuse-safe liveness checks, ancestor-protected kills      |
| [Markdown tables and linting](docs/tutorials/markdown.md)                    | `markdown`                                    | ANSI-aware table formatting and in-memory Markdown linting                   |
| [Durations and rate limiting](docs/tutorials/durations-and-rate-limiting.md) | `durations`, `ratelimit`                      | Duration parsing and formatting, sliding-window task rate limiting           |
| [View capture](docs/tutorials/view-capture.md)                               | `capture`, `httpd`                            | Headless-Chrome screenshots, UI tours, embedded static server                |
| [SQL anonymizer](docs/tutorials/sql-anonymizer.md)                           | `sql`                                         | Deterministic anonymization of SQL dumps                                     |
