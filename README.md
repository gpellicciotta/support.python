# Python Support Library

General-purpose Python support library and CLI, with as few third-party dependencies as possible.

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

See [docs/devops.md](docs/devops.md) for the full development and release workflow.

## Build

```bash
python -m pip install --upgrade build
python -m build
```

This creates both source (`dist/*.tar.gz`) and binary wheel (`dist/*.whl`) packages.
`python scripts/devops.py check` lints, tests, and builds through `.venv` in one step.
On GitHub pushes/PRs, the same artifacts are built (after lint and tests) by [python-package.yml](.github/workflows/python-package.yml).

## Installing the command-line tools
Installing the `support-python` package installs all standalone command-line tools:
- `processes` to list and safely kill processes
- `agent-digest` to create instruction files and skills that can be installed via `agent-files`
- `agent-files` to list and install or update agent instruction files
- `lint-markdown` to check (and fix) Markdown issues
- `git-repository-backup` to make local backups of entire git repositories

Upgrading from `v1.x`, where they ran as `support-python` subcommands or wrapper scripts? See [migration-v2.md](docs/migration-v2.md).

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
The `scripts/` directory also offers following additional - uninstalled - scripts:
- `extract-release-notes.py` to extract release notes from `CHANGELOG.md`
- `migrate-namespace.py` to migrate a project/repo's namespace
- `reset-history.py` to wipe and reset git history

Each acts on the Git repository containing the current directory, so run it from a support-python checkout against any repository:

```bash
cd path/to/other-repo
python path/to/support.python/scripts/extract-release-notes.py 1.2.3
python path/to/support.python/scripts/migrate-namespace.py --old acme --new widgets rewrite
python path/to/support.python/scripts/reset-history.py backup ../backups
```

Each script imports `support_python` from the checkout's `src/` directory, or from an installed package.

## Shared CLI helpers, tabular output, and session storage
`ToolHarness`/`Action`, `CliLogger`, tabular output, and session token storage: see the [CLI harness and logging tutorial](docs/tutorials/cli-harness-and-logging.md).

## Common script utilities
UTF-8 console setup, project version lookup, port checks, env files, and password hashing: see the [script utilities tutorial](docs/tutorials/script-utilities.md).

## CLI logging
`CliLogger` and log-level helpers: see the [CLI harness and logging tutorial](docs/tutorials/cli-harness-and-logging.md#cli-logging).

## REST client HTTP transport
`Transport`, `UrllibTransport`, `RawResponse`, and `TransportError`: see the [REST clients tutorial](docs/tutorials/rest-clients.md).

## REST client error hierarchy and status mapping
`ApiError` subclasses and `map_error`: see the [REST clients tutorial](docs/tutorials/rest-clients.md#error-hierarchy-and-status-mapping).

## DevOps script helpers and environment managers
`support_python.devops` provides subprocess step runners, local service managers, release helpers, `ReleasePipeline`,
and `DevopsCli` with Python, Gradle, and Node project adapters, a `deploy` action, and service action groups.
See the [DevOps scripts tutorial](docs/tutorials/devops-scripts.md).

## View Capture Engine and Static Server
Headless-Chrome view capture and the embedded static server: see the [view capture tutorial](docs/tutorials/view-capture.md).

## SQL Snapshot Anonymizer
Streaming, deterministic SQL dump anonymization: see the [SQL anonymizer tutorial](docs/tutorials/sql-anonymizer.md).

## Models and wire helpers
Wire datetimes, `WireEnum`, and server metadata models: see the [REST clients tutorial](docs/tutorials/rest-clients.md#models-and-wire-helpers).

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
Tri-state repository queries, porcelain parsing, and the Git runner: see the [Git helpers tutorial](docs/tutorials/git-helpers.md).

## Locking
File, null, Redis, and MySQL locks and `create_lock`: see the [files and locking tutorial](docs/tutorials/files-and-locking.md#locks).

## Process hierarchy and safe termination
Process trees, liveness checks, and `safe_kill`: see the [process management tutorial](docs/tutorials/process-management.md).

## Atomic text file helpers
Atomic UTF-8 writes and retrying replaces and reads: see the [files and locking tutorial](docs/tutorials/files-and-locking.md#atomic-text-files).

## Markdown table helpers
ANSI-aware GFM table helpers: see the [Markdown tutorial](docs/tutorials/markdown.md#table-helpers).

## Markdown linter
The `lint-markdown` CLI reads `.lint-markdown.json` (see [lint-markdown.md](docs/tools/lint-markdown.md)); the linter library API is in the [Markdown tutorial](docs/tutorials/markdown.md#linter).
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
Duration and timestamp parsing and formatting: see the [durations and rate limiting tutorial](docs/tutorials/durations-and-rate-limiting.md).

## Task rate limiter
`TaskRateLimiter`: see the [durations and rate limiting tutorial](docs/tutorials/durations-and-rate-limiting.md#task-rate-limiter).
