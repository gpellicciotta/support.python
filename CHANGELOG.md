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

## v2.0.47-pre
- CLI: Made `agent-files`, `lint-markdown`, and `git-repository-backup` accept configuration keys in kebab-case or snake_case with identical effect, via the new shared `normalize_config_keys`; a file setting both spellings uses the kebab-case value and logs one warning, and docs now show kebab-case keys ([config.py](src/support_python/config.py), [agent-files.md](docs/tools/agent-files.md), [lint-markdown.md](docs/tools/lint-markdown.md)).
- CLI: Made `lint-markdown` rule `MD011` allow up to two trailing spaces, so Markdown hard line breaks pass; it still flags three or more spaces and any trailing tab, and `fix` now trims longer runs to two spaces instead of stripping all trailing whitespace ([rules.py](src/support_python/markdown/rules.py), [lint.py](src/support_python/markdown/lint.py), [lint-markdown.md](docs/tools/lint-markdown.md)).
- CLI: Added `skill.references` to `agent-digest` front-matter: `generate` copies each listed file into its skill (rewriting Markdown links), and `check` reports `missing-reference`, `missing-skill-file`, `stale-skill-file`, and `unlisted-file` issues, with per-file statuses under `skills[].files` in JSON; listed files are no longer digest or skill sources, and files under a skill directory that are not listed now fail as `unlisted-file` instead of `orphan-file` ([agent_digest.py](src/support_python/tools/agent_digest.py), [agent-digest.md](docs/tools/agent-digest.md)).
- CLI: Made `git-repository-backup` find its user config through `user_config_path`, so Windows now reads `%APPDATA%/git-repository-backup/config.json` and `XDG_CONFIG_HOME` applies everywhere; the old `~/.config/git-repository-backup/config.json` is still read with a deprecation warning until v3.0.0 ([git_repository_backup.py](src/support_python/tools/git_repository_backup.py)).
- Library: Added `user_config_dir` and `user_config_path`, which resolve a tool's user configuration file through an absolute `XDG_CONFIG_HOME`, then `%APPDATA%` on Windows, then `~/.config` ([env.py](src/support_python/env.py)).
- Library: Made `parse_datetime` accept 1 to 6 fractional second digits and `+HH:MM`/`-HH:MM` offsets (converted to UTC), added `format_datetime(..., millis=True)`, and added `parse_date`/`format_date` for `YYYY-MM-DD` values; parsing now rejects non-zero-padded fields, lowercase `t`/`z`, and non-ASCII digits that `strptime` accepted ([dates.py](src/support_python/dates.py)).
- CLI: Made `--debug` imply `--verbose` in `ToolHarness`, so handlers reading `args.verbose` and `help --debug` behave as with `--verbose`; `--log-level` still sets the threshold ([cli.py](src/support_python/cli.py)).
- CLI: Added `--dry-run` to `agent-digest generate` and `--format text|json` to `agent-digest check`, whose JSON document lists digest and skill statuses and every issue, as [ADR-0003](docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md) requires ([agent_digest.py](src/support_python/tools/agent_digest.py), [agent-digest.md](docs/tools/agent-digest.md)).
- CLI: Added a shared JSON output mode: `CliLogger.json_output` sends every stdout-bound log message to stderr, `CliLogger.emit_json` prints one JSON document, and `ToolHarness.add_format_option` registers `--format text|json`, enabling the mode for `json` ([logging.py](src/support_python/logging.py), [cli.py](src/support_python/cli.py)).
- CLI: Switched `agent-files`, `lint-markdown`, `processes`, and `git-repository-backup` to the shared JSON mode, removing `StderrRoutingLogger`, `_JsonAwareLogger`, `LintMarkdownHarness`, `JsonModeLogger`, and `ProcessesHarness`; with `--format json`, `agent-files`, `lint-markdown`, and `git-repository-backup` now show their INFO lines and banners on stderr instead of dropping them, and JSON documents are unchanged.
- CLI: Fixed `ToolHarness` help option labels of 22 or more characters running into their help text; the option column now clears the longest label by two spaces and stays aligned ([cli.py](src/support_python/cli.py)).
- CLI: **[breaking]** Added `--version` and a working `--help` to `extract-release-notes`, `migrate-namespace`, `reset-history`, and `install-from-github-release` in [scripts](scripts/); the `--version` options of `migrate-namespace` and `reset-history reinit` are now `--new-version`.
- Docs: Restructured [README.md](README.md) into bootstrap, build, install, command-line tool, and library sections linking each tool page and tutorial, grouped [index.md](docs/index.md) by tools and tutorials, and refreshed the [devops.md](docs/devops.md) scripts table.
- Docs: Moved the README Git, locking, process, file, Markdown, duration, and rate limiter sections into five [docs/tutorials](docs/tutorials/) pages, and added a Markdown linter library example to [markdown.md](docs/tutorials/markdown.md).
- Docs: Moved the README CLI, logging, script utility, REST client, view capture, SQL anonymizer, and model sections into five [docs/tutorials](docs/tutorials/) pages, starting at [cli-harness-and-logging.md](docs/tutorials/cli-harness-and-logging.md).
- CLI: Aligned the `CliLogger.log_start` header with `ToolHarness`, now reading `Starting {name} v{version} with configuration:` ([logging.py](src/support_python/logging.py)).
- CLI: Printed the `Starting ... with configuration:` and `Finished ... with status: succeeded` lines on stdout only with `-v`/`--verbose`; they still reach the log file, and failed summaries still go to stderr ([cli.py](src/support_python/cli.py)).
- Docs: Moved the README DevOps helpers section into the [devops-scripts.md](docs/tutorials/devops-scripts.md) tutorial, the first page of a new `docs/tutorials/` folder.
- Docs: Added [migration-v2.md](docs/migration-v2.md), mapping every v1.x command, module, option, verb, and config file to its v2.0.0 replacement, and refreshed [CLAUDE.md](CLAUDE.md).
- CLI: **[breaking]** Rebuilt `run_capture_cli` on `ToolHarness` via the new `build_capture_harness`, replacing `build_capture_parser`; help and version use the harness format, no arguments shows help, `-v` means `--verbose`, invalid arguments exit 2, `list` output carries harness startup and completion lines, and log lines no longer carry a `cli_name` origin ([capture.py](src/support_python/capture.py)).
- CLI: **[breaking]** Removed `build_action_parser`, `print_help`, `print_version`, and `format_version` from `support_python.cli` and the package root in favor of `ToolHarness` ([cli.py](src/support_python/cli.py), [__init__.py](src/support_python/__init__.py)).
- DevEx: Added `DevopsCli.add_services`, registering opt-in `docker`, `db`, `server`, `mail`, and `client` action groups with sub-actions such as `devops db start`, plus `LocalVerifier.run_all_checks`, a `verify_deployment` `timeout`, and `<name>_test` snapshot targets such as `todos_test` in `LocalMySqlManager.load_snapshot` ([service_actions.py](src/support_python/devops/service_actions.py), [cli.py](src/support_python/devops/cli.py), [services.py](src/support_python/devops/services.py)).
- DevEx: Added a `deploy` action to `DevopsCli` via `set_deploy`, checking a clean tree, a released version, its `origin` tag at HEAD, and CI, then confirming, running `DeployStep`s, and verifying ([deploy.py](src/support_python/devops/deploy.py), [cli.py](src/support_python/devops/cli.py)).
- DevEx: Added `NodeProject`, running npm lint, format, test, build, and pack scripts and releasing the packed `dist/*.tgz` tarballs ([projects.py](src/support_python/devops/projects.py)).
- DevEx: Added `GradleProject`, running overridable Gradle wrapper tasks and optionally delegating `devops release` to a Gradle task via the new `Project.release` hook ([projects.py](src/support_python/devops/projects.py), [cli.py](src/support_python/devops/cli.py)).
- DevEx: Added `DevopsCli` with lint, format, test, build, check, clean, versions, and release actions over `Project`/`PythonProject` adapters, and rebuilt [devops.py](scripts/devops.py) on them ([cli.py](src/support_python/devops/cli.py), [projects.py](src/support_python/devops/projects.py)).
- DevEx: Added an optional post-freeze `build` hook to `ReleasePipeline`, so release assets carry the release version instead of `-pre` ([release.py](src/support_python/devops/release.py)).
- DevEx: Made `extract-release-notes.py`, `migrate-namespace.py`, and `reset-history.py` act on the current directory's Git repository via `support_python`, deleting `_repo_common.py`; `migrate-namespace.py finish` now publishes the frozen section as release notes ([extract-release-notes.py](scripts/extract-release-notes.py), [migrate-namespace.py](scripts/migrate-namespace.py), [reset-history.py](scripts/reset-history.py)).
- DevEx: Added `get_remote_url`, `parse_github_remote`, `get_github_repo`, and `get_default_branch` Git queries ([git.py](src/support_python/git.py)).
- DevEx: Added a dry-runnable `ReleasePipeline` that freezes, tags, pushes, publishes a GitHub release with assets, and reopens development, plus `confirm_typed` ([release.py](src/support_python/devops/release.py)).
- DevEx: Added `support_python.devops.release` with version-file, CHANGELOG.md freeze/reopen, release-notes, and GitHub-origin helpers ([release.py](src/support_python/devops/release.py)).
- CLI: Let `lint-markdown` load extra rules from plugins listed under the config `plugins` key or `--plugin`, and added a `rules` action listing every rule and its source ([plugins.py](src/support_python/markdown/plugins.py), [lint_markdown.py](src/support_python/tools/lint_markdown.py), [lint-markdown.md](docs/tools/lint-markdown.md)).
- CLI: **[breaking]** Made `agent-files` install an existing `./agent-digest.md` and `./agent-skills` without regenerating them, exiting 1 with an `agent-digest generate` hint when the digest is missing ([agent_files.py](src/support_python/tools/agent_files.py), [agent-files.md](docs/tools/agent-files.md)).
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
