# Versioned Changes

A summarized overview of all changes, per version of this project.

> Entries are in reverse chronological order, most recent at the top.
>
> A version actively being developed carries a `-pre` SemVer pre-release suffix on its heading (e.g.
> `## v0.1.1-pre`) instead of a status tag. Status codes used once a version leaves that state are:
> - `[{{date}}]` - frozen/finalized on {{date}}
> - `[released: {{date}}]` - released to package manager or production on {{date}}
> - `[broken]` - considered broken and not to be used
>
> Areas are the standard ones, plus `Library` for the `support_python` API.

---

## v2.0.4-pre
- Docs: Documented project-local `.venv` installs and the kept names whose v2 output changed in [migration-v2.md](docs/migration-v2.md).
- Library: Made the `DevopsCli` default description name `deploy` and the service groups that `set_deploy` and `add_services` enable ([cli.py](src/support_python/devops/cli.py)).
- Library: Reworded the `DevopsCli` exit code 1 text to say a prerequisite is missing, instead of naming the Python virtual environment for every adapter.
- Library: Made `DevopsCli` take help summaries and the `test` example from the project adapter, so `GradleProject` help names its Gradle tasks ([devops-scripts.md](docs/tutorials/devops-scripts.md)).
- Library: Made `devops release --skip-checks` warn that it has no effect on a project with its own release, such as a `GradleProject` with a `release_task`.

## v2.0.0 [released: 2026-11-10]
- CLI: Replaced the stale `update-global-agent-files.py` text in the `agent-files` begin marker, still syncing blocks with the old marker ([agent-files.md](docs/tools/agent-files.md)).
- CLI: Made `lint-markdown` `MD019` skip plan task files and ask for code spans for bare paths to missing files.
- CLI: Wrote help placeholders as `{{path}}` and `{{pid}}` in `agent-digest`, `agent-files`, and `processes`, replacing `<PATH>` and sample paths.
- CLI: **[breaking]** Made the `lint-markdown` `default` profile enable `MD015`, so `check` follows the Markdown guidelines without `--profile`.
- CLI: Fixed log files stamping entries in local time; `CliLogger` and `format_log_message` now write UTC ([logging.py](src/support_python/logging.py)).
- Library: Added `Setting`, `SettingsSchema`, `resolve_settings`, and `add_config_actions`, giving tools guideline precedence and a standard `config` group ([config.py](src/support_python/config.py)).
- Library: Added `user_config_dir` and `user_config_path`, resolving user config through `XDG_CONFIG_HOME`, `%APPDATA%`, or `~/.config` ([env.py](src/support_python/env.py)).
- Config: Made `agent-files`, `lint-markdown`, and `git-repository-backup` accept kebab-case or snake_case keys, reporting unknown keys in kebab-case.
- CLI: Made `lint-markdown` rule `MD011` accept two trailing spaces as a hard line break ([lint-markdown.md](docs/tools/lint-markdown.md)).
- Library: Made `parse_datetime` accept 1 to 6 fractional digits and UTC offsets, reject malformed fields, and added `parse_date`/`format_date`.
- CLI: Made `--debug` imply `--verbose`, and showed startup and finish lines on `stdout` only with `--verbose`.
- Library: Changed the `CliLogger.log_start` header to `Starting {{name}} v{{version}} with configuration:`, matching `ToolHarness` ([logging.py](src/support_python/logging.py)).
- Library: Added a JSON mode to `CliLogger` and `ToolHarness.add_format_option`, keeping `stdout` free of log lines.
- CLI: Added `--format text|json` to the listing and checking actions of every tool, with log lines on `stderr`.
- CLI: Fixed misaligned `ToolHarness` help text for option labels of 22 or more characters ([cli.py](src/support_python/cli.py)).
- DevEx: **[breaking]** Added `--version` and `--help` to repository [scripts](scripts/), renaming their former `--version` options to `--new-version`.
- CLI: **[breaking]** Rebuilt `run_capture_cli` on `ToolHarness` through `build_capture_harness`, replacing `build_capture_parser` ([capture.py](src/support_python/capture.py)).
- DevEx: Added opt-in `docker`, `db`, `server`, `mail`, and `client` action groups to `DevopsCli` through `add_services`.
- DevEx: Added a `deploy` action that checks the tree, version, tag, and CI before running `DeployStep`s ([deploy.py](src/support_python/devops/deploy.py)).
- DevEx: Added `DevopsCli` with standard actions over `PythonProject`, `GradleProject`, and `NodeProject`, and rebuilt [devops.py](scripts/devops.py) on it.
- DevEx: Added `ReleasePipeline`, which freezes, tags, pushes, and publishes GitHub releases with typed confirmation and `--dry-run` ([release.py](src/support_python/devops/release.py)).
- DevEx: Made `extract-release-notes.py`, `migrate-namespace.py`, and `reset-history.py` act on the current directory's Git repository.
- Library: Added `get_remote_url`, `parse_github_remote`, `get_github_repo`, and `get_default_branch` Git queries ([git.py](src/support_python/git.py)).
- CLI: Added `agent-digest`, generating and checking a size-budgeted digest and skills from Markdown paths ([agent-digest.md](docs/tools/agent-digest.md)).
- CLI: **[breaking]** Made `agent-files` `sync` and `check` install an existing digest, replacing `update` and `diff` ([agent-files.md](docs/tools/agent-files.md)).
- CLI: **[breaking]** Replaced `lint-markdown --fix` with a `fix` action, and added `rules`, rule plugins, and `.lint-markdown.json` config.
- CLI: **[breaking]** Renamed `processes list --format table` to `--format text`, and added `kill --dry-run` ([processes.md](docs/tools/processes.md)).
- CLI: **[breaking]** Renamed `backup-git-repos` to `git-repository-backup`, with legacy config fallbacks ([git-repository-backup.md](docs/tools/git-repository-backup.md)).
- Library: **[breaking]** Removed `build_action_parser`, `print_help`, `print_version`, `format_version`, `ToolLogger`, and `TeeLogger` for `ToolHarness` and `CliLogger`.
- Library: Configured UTF-8 output streams in `ToolHarness.run`, so tools print non-ASCII text on any console.
- Library: **[breaking]** Moved tool modules into `support_python.tools`, and split `markdown_lint` into `support_python.markdown` and `tools.lint_markdown`.
- Library: **[breaking]** Split `support_python.devops` into `steps` and `services` modules, so tests must patch the new paths.
- CLI: **[breaking]** Replaced the `support-python` command with five console scripts, mapped in [migration-v2.md](docs/migration-v2.md).
- Docs: Split [README.md](README.md) into tool references under [docs/tools](docs/tools/) and library tutorials under [docs/tutorials](docs/tutorials/).
- Docs: Recorded [ADR-0003-standalone-tools-and-reusable-devops.md](docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md) on standalone tools and reusable devops.

---

## v1.3.5 [2026-11-08]
- CLI: Added standalone `scripts/lint-markdown.py` and `scripts/agent-files.py` wrapper scripts.
- CLI: Added the `processes` CLI and `scripts/processes.py` script with `kill` and filtered `list` subcommands.
- CLI: Split Markdown lint rules into [rules.py](src/support_python/markdown/rules.py), [registry.py](src/support_python/markdown/registry.py), [profiles.py](src/support_python/markdown/profiles.py), and [tables.py](src/support_python/markdown/tables.py).

---

## v1.3.0 [2026-11-07]
- CLI: Parameterized agent-files sync with JSON configs, CLI flags, and `ToolRegistry` in `src/support_python/agent_files_config.py` and `docs/agent-files.md`.
- CLI: Ported global agent-files sync in `src/support_python/agent_files.py` and exposed `support-python agent-files` in [cli.py](src/support_python/cli.py).
- CLI: Ported `MarkdownLinter` in `src/support_python/markdown_lint.py` and exposed `support-python lint markdown` in [cli.py](src/support_python/cli.py).
- CLI: Consolidated `ToolHarness` and `CliLogger` in [cli.py](src/support_python/cli.py) and [logging.py](src/support_python/logging.py), and added `support-python backup` in `src/support_python/backup.py`.
- DevEx: Added `stream_subprocess`, `run_step_command`, `resolve_executable`, and `EXIT_COMMAND_NOT_FOUND` in `src/support_python/devops.py` for logged subprocess streaming.
- CLI: Unified `CliLogger`, `ToolLogger`, `TeeLogger`, `ToolHarness`, and build-metadata version helpers in [logging.py](src/support_python/logging.py) and [cli.py](src/support_python/cli.py).
- BackEnd: Added sliding-window `TaskRateLimiter` in [ratelimit.py](src/support_python/ratelimit.py) to cap task dispatches across configurable time windows.
- BackEnd: Added duration parsing, human-readable duration formatting, and relative epoch formatting helpers in [durations.py](src/support_python/durations.py).
- DevEx: Expanded `CloudSqlProxyManager` to locate `cloud-sql-proxy` outside `PATH` and fail cleanly when Docker is missing.
- BackEnd: Added ANSI-aware Markdown table formatting, row splitting, and alignment check helpers in [tables.py](src/support_python/markdown/tables.py).
- BackEnd: Added atomic UTF-8 text write, replacement, and retry-hardened read helpers in [files.py](src/support_python/files.py).
- BackEnd: Added OS process hierarchy, start time, liveness, termination, and ancestor-protected `safe_kill` helpers.
- BackEnd: Added Git execution and repository queries with explicit failure results and porcelain parsing.
- BackEnd: Added locking with a `Lock` base class, re-entrant `FileLock`, `NullLock`, and a `create_lock` backend factory.
- BackEnd: Added distributed `RedisLock` with atomic `SET NX PX` and Lua release script as an optional extra.
- BackEnd: Added distributed `MySQLLock` using server-side advisory locks as an optional extra.
- DevEx: Added `install-from-github-release.py`, a stdlib-only script that installs a released wheel from any GitHub repository.

---

## v1.0.0 [released: 2026-10-31]
- CLI: Added `CliLogger` and `LogLevel` for guideline-compliant CLI logging with severity indicators and log files.
- CLI: Added `build_action_parser`, `print_version`, and `print_help` for action-oriented command-line tools.
- CLI: Added table rendering, file-backed session token storage, env-file parsing, and UTF-8 console setup.
- BackEnd: Added a stdlib-only REST transport with a typed error hierarchy and status-code mapping.
- BackEnd: Added wire date helpers, `WireEnum`, and standard server metadata models.
- BackEnd: Added a streaming SQL snapshot anonymizer with deterministic masking and custom table transformers.
- BackEnd: Added `ViewCaptureEngine` for headless-Chrome screenshots, an embedded static server, and UI tour reports.
- Security: Added standard password hashing and property decryption in `crypto`.
- DevEx: Added Docker, MySQL, server, mail, and Cloud SQL proxy managers plus `run_step` in `devops`.
- DevEx: Required explicit MySQL passwords and a Cloud SQL instance, with no built-in defaults.
- DevEx: Added bootstrap, devops, kill-processes, backup-git-repos, and release-notes scripts.
- Build: Added src-layout setuptools packaging for Python 3.9+, ruff linting, pytest, and GitHub Actions build and release.
- Docs: Documented the public API with Google-style docstrings, a README, requirements, and a DevOps guide.
