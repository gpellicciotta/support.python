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

## v3.0.0 [released: 2026-11-11]
- Library: Documented every public module, class, function, method, and `__init__` in `src/`, and enabled ruff `D100`-`D107` for `src/` so missing docstrings fail the lint ([pyproject.toml](pyproject.toml)).
- Docs: Added `docs/specs/` with the config file formats of `agent-files`, `lint-markdown`, and `git-repository-backup`, the `agent-digest` front-matter, and every `--format json` document ([specs](docs/specs/json-output.md), [index.md](docs/index.md)).
- CLI: Added `--format text|json` to `git-repository-backup backup` and `restore`, reporting each repository and layer outcome, and the restore source, target, and branch ([git_repository_backup.py](src/support_python/tools/git_repository_backup.py), [git-repository-backup.md](docs/tools/git-repository-backup.md)).
- CLI: Added `--format text|json` to `lint-markdown fix`, reporting each fixed file with its fixes and every remaining issue in the `check` issue shape ([lint_markdown.py](src/support_python/tools/lint_markdown.py), [lint-markdown.md](docs/tools/lint-markdown.md)).
- CLI: Added `--format text|json` to `agent-files sync`, reporting each tool's planned or applied instruction-file and skill changes as `synced`, `changes-pending`, `failed`, `unavailable`, or `up-to-date` ([agent_files.py](src/support_python/tools/agent_files.py), [agent-files.md](docs/tools/agent-files.md)).
- CLI: **[breaking]** Moved `agent-files` settings onto the shared resolver, adding `AGENT_FILES_*` variables, user and system config files, and the `config` action; `tools` merge across sources by name, and unknown keys, malformed files, and invalid values now warn instead of exiting `2` ([agent_files.py](src/support_python/tools/agent_files.py), [agent_files_config.py](src/support_python/tools/agent_files_config.py), [agent-files.md](docs/tools/agent-files.md), [migration-v2.md](docs/migration-v2.md)).
- Library: Added `Setting.normalize` for converting raw values before parsing, and `AGENT_FILES_SETTINGS`, `build_schema`, and an `environ` parameter to `agent_files_config` ([config.py](src/support_python/config.py), [agent_files_config.py](src/support_python/tools/agent_files_config.py), [configuration.md](docs/tutorials/configuration.md)).
- CLI: **[breaking]** Moved `lint-markdown` settings onto the shared resolver, adding `LINT_MARKDOWN_*` variables, user and system config files, and the `config` action; list settings now replace across sources, malformed files and invalid values warn instead of exiting `2`, and the `rules` map form is library-only ([lint_markdown.py](src/support_python/tools/lint_markdown.py), [profiles.py](src/support_python/markdown/profiles.py), [lint-markdown.md](docs/tools/lint-markdown.md), [migration-v2.md](docs/migration-v2.md)).
- Library: Added `Setting.aliases` for alternative file keys, and `PROFILE_SETTINGS`, `build_schema`, `apply_profile_settings`, and `profile_from_settings` to `support_python.markdown.profiles` ([config.py](src/support_python/config.py), [profiles.py](src/support_python/markdown/profiles.py), [markdown.md](docs/tutorials/markdown.md)).
- CLI: **[breaking]** Moved `git-repository-backup` settings onto the shared resolver, adding `GIT_REPOSITORY_BACKUP_*` variables, a system config file, and the `config` action; unknown keys, malformed files, and invalid values now warn instead of exiting `2` ([git_repository_backup.py](src/support_python/tools/git_repository_backup.py), [git-repository-backup.md](docs/tools/git-repository-backup.md), [migration-v2.md](docs/migration-v2.md)).
- Library: Made `add_config_actions` skip its `get --source` flag when the harness already has a global `--source` option ([config.py](src/support_python/config.py), [configuration.md](docs/tutorials/configuration.md)).
- CLI: Added `--format text|json` to `agent-digest generate`, reporting each digest and skill file as created, updated, or unchanged ([agent_digest.py](src/support_python/tools/agent_digest.py), [agent-digest.md](docs/tools/agent-digest.md)).
- CLI: Added `--format text|json` to `processes kill`, reporting each killed, skipped, not-found, and failed PID as one JSON document ([processes.py](src/support_python/tools/processes.py), [processes.md](docs/tools/processes.md)).
- Library: Added `safe_kill_report` returning the per-PID outcomes of `safe_kill` ([processes.py](src/support_python/processes.py), [process-management.md](docs/tutorials/process-management.md)).
- CLI: **[breaking]** Made `processes kill` ask for a typed confirmation, skippable with `--yes`, and exit `2` without `--yes` when `stdin` is not a terminal ([processes.py](src/support_python/tools/processes.py), [processes.md](docs/tools/processes.md), [migration-v2.md](docs/migration-v2.md)).
- CLI: Made `ToolHarness` `help --verbose` list each action's positional arguments and options with metavars, and lowercased option help text ([cli.py](src/support_python/cli.py), [cli-harness-and-logging.md](docs/tutorials/cli-harness-and-logging.md)).
- Library: Added constructor parameters for the support.java flags, commands, health endpoint, running status, assets, and snapshot env-file names to the devops service managers ([services.py](src/support_python/devops/services.py), [devops-scripts.md](docs/tutorials/devops-scripts.md)).
- Library: **[breaking]** Made `decrypt_property_value` raise `ImportError` when `cryptography` is missing and `ValueError` when an `aes:` value fails to decrypt, instead of returning the ciphertext ([crypto.py](src/support_python/crypto.py), [migration-v2.md](docs/migration-v2.md)).
- Library: **[breaking]** Removed `STANDARD_SALT` and `DEFAULT_AES_KEY_HEX`, making the salt of `get_standard_password_hash` (keyword-only) and the key of `decrypt_property_value` required and validated ([crypto.py](src/support_python/crypto.py), [migration-v2.md](docs/migration-v2.md)).
- Library: **[breaking]** Removed the `auth` and `counters` schema transformers and the `app` and `custom_password` parameters from the SQL anonymizer, which now requires a `transformers` map ([sql.py](src/support_python/sql.py), [migration-v2.md](docs/migration-v2.md)).
- Library: **[breaking]** Made `LocalMySqlManager` take `snapshot_transformers`, refuse to snapshot without them, and drop `custom_password` and `db snapshot --custom-password` ([services.py](src/support_python/devops/services.py)).
- Library: Added declarative column-rule transformer builder and public SQL value helpers to the SQL anonymizer ([sql.py](src/support_python/sql.py)).
- Library: Added `test --slow` to `DevopsCli` and made `check` run both fast and slow suites ([cli.py](src/support_python/devops/cli.py)).
- Test: Split test suite into parallel fast suite and marked slow suite with timeouts ([pyproject.toml](pyproject.toml)).
- CLI: **[breaking]** Resolved GitHub repository links to sibling checkouts only for configured github-owners, defaulting to none ([lint.py](src/support_python/markdown/lint.py)).
- Library: **[breaking]** Defaulted APP_AUTHOR and COPYRIGHT to empty, omitting the banner copyright suffix when empty, while bundled tools keep theirs ([cli.py](src/support_python/cli.py)).
- Library: Derived version build metadata only from support-python checkouts or install metadata, not enclosing repositories ([cli.py](src/support_python/cli.py)).
- Library: Made `ToolHarness` map a trailing `rc0` version suffix back to `-pre` ([cli.py](src/support_python/cli.py)).
- CLI: Retried external link checks with GET when HEAD returns 404 in `lint-markdown` ([lint.py](src/support_python/markdown/lint.py)).
- CLI: Made agent-files sync --dry-run --no-prune report kept stale skills instead of removals ([agent_files.py](src/support_python/tools/agent_files.py)).
- CLI: Made every tool's `--version` report the installed `support-python` version instead of the current directory's project version ([cli.py](src/support_python/cli.py)).
- DevEx: Added a conftest session fixture redirecting user environment variables and failing tests that write real state ([conftest.py](tests/conftest.py)).
- CLI: Fixed `agent-digest generate` failing on Python 3.9, which rejects the `newline` argument of `Path.write_text` ([agent_digest.py](src/support_python/tools/agent_digest.py)).
- Build: Ran the Python 3.9 CI job on `ubuntu-24.04`, since `setup-python` has no 3.9 for `ubuntu-latest` ([python-package.yml](.github/workflows/python-package.yml)).
- CLI: Fixed `lint-markdown` `MD014` skipping root-relative links such as `/docs/guide.md` on Linux and macOS ([rules.py](src/support_python/markdown/rules.py)).
- Library: Added `capture_options` and `prepare_capture` hooks to `CaptureAppConfig`, so capture CLIs can add app-specific options ([view-capture.md](docs/tutorials/view-capture.md)).
- Library: Made `ToolHarness` run its fallback action when the command line starts with an option, as `run_capture_cli` already did ([cli.py](src/support_python/cli.py)).
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
