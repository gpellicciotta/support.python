<!-- BEGIN plan (managed by plan init) -->
This project tracks its work with plan in `PLAN.md` and `.plan/tasks/`.
Load the `plan-task-usage-guidelines` skill before creating, starting, or changing tasks.
Change `PLAN.md` and task frontmatter only through `plan` commands.
<!-- END plan -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is
`support-python` is a general-purpose Python support library and CLI for Python clients and ops scripts. It aims to have as few
third-party dependencies as possible so downstream consumers aren't burdened by transitive dependencies.
Currently it provides guideline-compliant CLI logging (`CliLogger`/`LogLevel`), a shared CLI version/help
argparse helper (`build_action_parser`/`print_version`/`print_help`), a stdlib-only REST-client HTTP
transport (`Transport`/`UrllibTransport`/`RawResponse`/`TransportError`/`build_query_string`), and a narrow
devops-script step runner (`run_step`); further modules are meant to be pulled out of hand-duplicated
code as shared-library candidates are reviewed and approved (see `PLAN.md` and [ADR-0003-standalone-tools-and-reusable-devops.md](docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md)).

## Commands
All commands use the project's venv (`.venv`, created via `python -m venv .venv` — or run
`python scripts/bootstrap-dev-environment.py` for a one-shot bootstrap: creates the venv, installs editable +
dev extras, lints, tests, builds sdist/wheel):
- Install in editable mode, with the `dev` extra (pytest, ruff, build):
  `.venv\Scripts\pip install -e ".[dev]"`
- Lint: `.venv\Scripts\ruff check .` / `.venv\Scripts\ruff format --check .`
- Run the test suite: `.venv\Scripts\python -m pytest` (or `python -m unittest discover -s tests`)
- Run the standalone CLIs (once installed): `.venv\Scripts\processes`, `.venv\Scripts\agent-files`,
  `.venv\Scripts\lint-markdown`, and `.venv\Scripts\git-repository-backup`.

Dependencies are declared once, in [pyproject.toml](pyproject.toml) — there is no separate `requirements.txt` to keep in sync.

## Architecture
Modules under `src/support_python/` (library symbols are re-exported from the package root; tool modules under `support_python.tools` are not re-exported):
- [logging.py](src/support_python/logging.py): `LogLevel`, `CliLogger` (`ToolLogger`/`TeeLogger` aliases), `resolve_log_level`/`normalize_log_level`, `format_severity_indicator`/`format_log_message`, and `init_cli_logger` — unified guideline-compliant CLI logging.
- [cli.py](src/support_python/cli.py): `ToolHarness`, `Action`, `get_full_version`/`resolve_build_metadata`, and `build_action_parser`/`print_version`/`print_help` — shared action-oriented CLI harness and argparse helpers.
- [agent_files.py](src/support_python/tools/agent_files.py), [agent_files_config.py](src/support_python/tools/agent_files_config.py): deterministic global agent-files and skills synchronization (`SyncHarness`, `Tool`, `AgentFilesConfig`, `ToolRegistry`, `load_agent_files_config`) exposed via `agent-files` (see [agent-files.md](docs/tools/agent-files.md)).
- [net.py](src/support_python/net.py): stdlib-only REST-client transport (`Transport`, `UrllibTransport`, `RawResponse`,
  `TransportError`, `build_query_string`) and `is_port_in_use`. A non-2xx response is a normal `RawResponse`.
- [git.py](src/support_python/git.py): Git runner and repository queries; failures return `None`, distinct from confirmed `False` results.
- [locking.py](src/support_python/locking.py): `Lock` ABC, re-entrant `FileLock`, `NullLock`, `RedisLock`, `MySQLLock`, `LockTimeoutError`, and the `create_lock` backend factory.
- [processes.py](src/support_python/processes.py), [tools/processes.py](src/support_python/tools/processes.py), [git_repository_backup.py](src/support_python/tools/git_repository_backup.py): process hierarchy, start-time lookup, PID-reuse-safe liveness checks, termination, ancestor-protected `safe_kill`, and the `processes` and `git-repository-backup` CLIs.
- [files.py](src/support_python/files.py): atomic UTF-8 text writes via sibling temporary files, Windows-safe `atomic_replace` retries, and `read_text_retrying`.
- [tables.py](src/support_python/markdown/tables.py), [registry.py](src/support_python/markdown/registry.py), [rules.py](src/support_python/markdown/rules.py), [profiles.py](src/support_python/markdown/profiles.py), [markdown_lint.py](src/support_python/markdown_lint.py): ANSI-aware Markdown table formatting (`format_markdown_table`, `format_markdown_table_block`, `check_table_alignment`) and rule-based Markdown linting (`MarkdownLinter`, `RuleRegistry`, `LintProfile`, `load_profile`) exposed via `lint-markdown` (see [markdown-lint.md](docs/markdown-lint.md)).
- [durations.py](src/support_python/durations.py): duration and timestamp parsing (`parse_duration_to_seconds`, `parse_iso8601`, `parse_date_or_datetime`) and human-readable/epoch formatting (`format_duration`, `format_short_duration`, `format_epoch`, `format_past_epoch`).
- [ratelimit.py](src/support_python/ratelimit.py): sliding-window task dispatch rate limiter (`TaskRateLimiter`) with injectable `now` timestamps and a 1-second minimum wait duration when blocked.
- [errors.py](src/support_python/errors.py): REST-client exception hierarchy and status-code mapping helpers.
- [__init__.py](src/support_python/devops/__init__.py), [steps.py](src/support_python/devops/steps.py), [services.py](src/support_python/devops/services.py): `stream_subprocess`, `run_step_command`, `resolve_executable`, `EXIT_COMMAND_NOT_FOUND`, and `run_step` in `devops.steps` plus Docker, MySQL, mail, server, and Cloud SQL proxy managers (including non-`PATH` proxy discovery) in `devops.services`, re-exported from `support_python.devops`.
  Pin it via a consumer's own `scripts/requirements.txt`, never from a bootstrap script
  (see [ADR-0001-devops-scripts-toolkit-scope.md](docs/adrs/ADR-0001-devops-scripts-toolkit-scope.md) and [ADR-0003-standalone-tools-and-reusable-devops.md](docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md)).
- [capture.py](src/support_python/capture.py), [httpd.py](src/support_python/httpd.py): headless-Chrome view capture and the embedded static HTTP server.
- [sql.py](src/support_python/sql.py): streaming SQL snapshot anonymizer. [crypto.py](src/support_python/crypto.py): password hashing and property decryption.
- [dates.py](src/support_python/dates.py), [models.py](src/support_python/models.py), [tables.py](src/support_python/tables.py), [tokens.py](src/support_python/tokens.py), [env.py](src/support_python/env.py), [terminal.py](src/support_python/terminal.py), [version.py](src/support_python/version.py): wire dates and
  models, table rendering, token storage, env-file parsing, UTF-8 console setup, and project version lookup.

## Development Guidelines
This repository follows the cross-project
[Development Guidelines](https://github.com/gpellicciotta/dev-guidelines):
- Use [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`); backward-incompatible changes require a major version bump and an explicit `**[breaking]**` note in [CHANGELOG.md](CHANGELOG.md).
- Favour simplicity over ingenuity. Keep things as simple as possible for what's actually needed today — don't
  design for hypothetical future requirements.
- Minimize third-party dependencies. Reach for the standard library first; add a dependency only when it earns
  its ongoing maintenance cost.
- Make it easy to get started: a clone + `python scripts/bootstrap-dev-environment.py` (or the commands under
  Commands above) should be enough to get a working venv, passing tests, and a build — no undocumented setup
  steps.
- Use the same tools and techniques the rest of the Python ecosystem is using (src-layout, [pyproject.toml](pyproject.toml),
  pytest, ruff, GitHub Actions) unless there's a concrete reason to deviate.
- CLI design: prefer action-oriented, subcommand-based CLIs (`tool action [options]`). Provide `help` action /
  `-h` / `--help`, `version` action / `--version`, `--verbose` option, and standardized `{name} v{version} -
  {copyright}` header with exit codes.

## Conventions
- [CHANGELOG.md](CHANGELOG.md) (top-level) tracks version history; the top heading carries a `-pre` SemVer suffix while
  under active development (e.g. `## v2.0.0-pre`), replaced with a status tag (`[YYYY-MM-DD]` /
  `[released: YYYY-MM-DD]` / `[broken]`) at freeze/release time. [pyproject.toml](pyproject.toml)'s `version` must always
  match the top heading exactly, `-pre` included.
- `PLAN.md` and `.plan/tasks/` track tasks; change them only through `plan` commands.
- Mandatory docs: [index.md](docs/index.md), [requirements.md](docs/requirements.md), and [devops.md](docs/devops.md).
- Keep [README.md](README.md)'s build/install/usage sections in sync with the code as it evolves — treat drift there as a
  bug, not a documentation nice-to-have.
- Style guide: spaces for indentation (never tabs), 4-space indent width, 132-character line length, UTF-8
  everywhere. Enforced by [.editorconfig](.editorconfig) (editor-level) and `ruff` ([pyproject.toml](pyproject.toml)'s `[tool.ruff]`, run via
  `ruff check .` / `ruff format --check .`, wired into CI) — don't let either drift from these numbers.
