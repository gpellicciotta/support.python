# Versioned Changes

A summarized overview of all changes, per version of this project.

> Entries are in reverse chronological order, most recent at the top.
>
> A version actively being developed carries a `-pre` SemVer pre-release suffix on its heading (e.g.
> `## v0.1.1-pre`) instead of a status tag. Status codes used once a version leaves that state are:
> - `[{{date}}]` - frozen/finalized on {{date}}
> - `[released: {{date}}]` - released to package manager or production on {{date}}
> - `[broken]` - considered broken and not be used

---

## v2.0.17-pre
- CLI: **[breaking]** Renamed `processes list --format table` to `--format text`, added `kill --dry-run`, and kept JSON `stdout` log-free ([processes.py](src/support_python/tools/processes.py), [processes.md](docs/tools/processes.md)).
- CLI: **[breaking]** Dropped `lint-markdown --fix`, added `fix --dry-run` and `check --format text|json`, and defaulted config to `.lint-markdown.json` ([lint_markdown.py](src/support_python/tools/lint_markdown.py), [profiles.py](src/support_python/markdown/profiles.py)).
- CLI: **[breaking]** Generalized `agent-digest` to take `<PATH>...` inputs, order by `index` front-matter, and fold `validate` into `check` ([agent_digest.py](src/support_python/tools/agent_digest.py), [agent-digest.md](docs/tools/agent-digest.md)).
- CLI: Ported the agent digest generator into [agent_digest.py](src/support_python/tools/agent_digest.py) with the `agent-digest` console script and packaged loading in [agent_files.py](src/support_python/tools/agent_files.py).
- CLI: **[breaking]** Made `sync` and `check` canonical in `agent-files` (removing `update` and `diff`), added `--format text|json`, and defaulted config to `.agent-files.json` ([agent_files.py](src/support_python/tools/agent_files.py), [agent_files_config.py](src/support_python/tools/agent_files_config.py)).
- CLI: **[breaking]** Configured UTF-8 streams in `ToolHarness.run` and removed `ToolLogger` and `TeeLogger` aliases in favor of `CliLogger` ([cli.py](src/support_python/cli.py), [logging.py](src/support_python/logging.py)).
- CLI: **[breaking]** Renamed `backup-git-repos` to `git-repository-backup` in [git_repository_backup.py](src/support_python/tools/git_repository_backup.py) ([git-repository-backup.md](docs/tools/git-repository-backup.md)), with legacy config fallback and `list --format text|json`.
- CLI: **[breaking]** Split `support_python.markdown_lint` into [lint.py](src/support_python/markdown/lint.py) (import from `support_python.markdown`) and [lint_markdown.py](src/support_python/tools/lint_markdown.py) (CLI in `support_python.tools.lint_markdown`).
- CLI: **[breaking]** Moved `cli_processes`, `agent_files`, `agent_files_config`, and `backup` into `support_python.tools` ([processes.py](src/support_python/tools/processes.py), [agent_files.py](src/support_python/tools/agent_files.py), [agent_files_config.py](src/support_python/tools/agent_files_config.py), [git_repository_backup.py](src/support_python/tools/git_repository_backup.py)).
- CLI: **[breaking]** Replaced `support-python` and wrapper scripts with `processes`, `agent-files`, `agent-digest`, `lint-markdown`, and `git-repository-backup` console scripts in [pyproject.toml](pyproject.toml).
- DevEx: **[breaking]** Split `support_python.devops` into [steps.py](src/support_python/devops/steps.py) and [services.py](src/support_python/devops/services.py) with [devops/__init__.py](src/support_python/devops/__init__.py) re-exports; mock patch targets moved from `support_python.devops.<name>` to `support_python.devops.steps.<name>` or `support_python.devops.services.<name>` (e.g. `support_python.devops.services.is_port_in_use`, `support_python.devops.services.signal.signal`).
- Docs: Recorded [ADR-0003-standalone-tools-and-reusable-devops.md](docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md) on standalone CLI tools, uniform CLI conventions, and reusable `support_python.devops`.

---

## v1.3.5 [2026-11-08]
- CLI: Added standalone `scripts/lint-markdown.py` and `scripts/agent-files.py` wrapper scripts.
- CLI: Added the `processes` CLI and `scripts/processes.py` script with `kill` and filtered `list` subcommands.
- CLI: Split Markdown lint rules into [rules.py](src/support_python/markdown/rules.py), [registry.py](src/support_python/markdown/registry.py), [profiles.py](src/support_python/markdown/profiles.py), and [tables.py](src/support_python/markdown/tables.py).

---

## v1.3.0 [2026-11-07]
- CLI: Parameterized agent-files sync with JSON configs, CLI flags, and `ToolRegistry` in [agent_files_config.py](src/support_python/agent_files_config.py) and [agent-files.md](docs/agent-files.md).
- CLI: Ported global agent-files sync in [agent_files.py](src/support_python/agent_files.py) and exposed `support-python agent-files` in [cli.py](src/support_python/cli.py).
- CLI: Ported `MarkdownLinter` in [markdown_lint.py](src/support_python/markdown_lint.py) and exposed `support-python lint markdown` in [cli.py](src/support_python/cli.py).
- CLI: Consolidated `ToolHarness` and `CliLogger` in [cli.py](src/support_python/cli.py) and [logging.py](src/support_python/logging.py), and added `support-python backup` in [backup.py](src/support_python/backup.py).
- DevEx: Added `stream_subprocess`, `run_step_command`, `resolve_executable`, and `EXIT_COMMAND_NOT_FOUND` in [devops.py](src/support_python/devops.py) for logged subprocess streaming.
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
