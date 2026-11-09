# Requirements

Functional and technical requirements for the `support-python` project.

---

## High-Level Goals
- Provide a general-purpose Python support library and five standalone CLI tools (`processes`, `agent-files`,
  `agent-digest`, `lint-markdown`, `git-repository-backup`), usable across projects with as few third-party
  dependencies as possible so downstream consumers aren't burdened by transitive dependencies.
- Serve as the shared foundation for Python clients, developer tools, and thin project `devops.py`
  runners in `scripts/` that would otherwise each carry their own copy of the same helpers.
- Distribute releases as an installable Git dependency with attached GitHub Release packages.

---

## Functional Requirements

### Logging
- Provide `CliLogger`/`LogLevel` and formatting helpers (`format_log_message`/`format_severity_indicator`),
  guideline-compliant and API-similar to the logging package in support.java, targeting
  simple CLI tools rather than long-running services.

### Dates and Wire Serialization
- Provide wire datetime parsing and formatting (`parse_datetime`, `format_datetime`, `from_wire_date`, `to_wire_date`)
  strictly adhering to UTC `yyyy-MM-dd'T'HH:mm:ss'Z'` format (`support_python.dates`).

### Cryptography
- Provide deterministic password hash computation matching service authentication standards (`get_standard_password_hash`)
  and AES-CBC encrypted property decryption (`decrypt_property_value`) in `support_python.crypto`.

### CLI and Standalone Tools
- Provide a shared, reusable CLI harness (`ToolHarness`, `Action`, `build_action_parser`/`print_version`/`print_help`) for
  guideline-compliant, action-oriented CLIs: `-h`/`--help`, `-v`/`--version`, `--verbose`/`--debug`, the
  standard `{prog} v{version} - Copyright (c) {author}` header, centralized UTF-8 console output setup, and standard
  exit codes (`0` success, `1` failure or `check` findings, `2` invalid arguments) in `support_python.cli`, with no umbrella `support-python` command or `python -m support_python` entry point.
- Provide five standalone console scripts (`processes`, `agent-files`, `agent-digest`, `lint-markdown`,
  `git-repository-backup`) implemented under `support_python.tools.<snake_name>` with uniform CLI conventions:
  `list`/`check`/write verbs, `--dry-run` on write actions, `--format text|json` on `list` and `check`, and
  `--config` overrides for project-scoped (`./.<tool-name>.json`) and user-scoped (`~/.config/<tool-name>/config.json`)
  configuration files (see [ADR-0003-standalone-tools-and-reusable-devops.md](adrs/ADR-0003-standalone-tools-and-reusable-devops.md)).
- Provide tabular formatting (`format_table`) and structured output rendering (`render_output`, `json_serial`)
  supporting human-readable tables, dataclass lists, dictionaries, and JSON output formatting (`support_python.tables`).
- Provide pluggable session persistence (`TokenStore`, `FileTokenStore`) for CLI tools requiring multi-invocation
  state and session token retention under safe user directory paths (`support_python.tokens`).

### Common Script Utilities
- Provide TCP socket inspection (`is_port_in_use` in `support_python.net`), cross-platform terminal UTF-8 output configuration
  (`configure_utf8_output` in `support_python.terminal`), project version discovery across Gradle/pyproject configs
  (`get_project_version` in `support_python.version`), and properties/.env file parsing (`read_env_file` in `support_python.env`).
- Provide focused, composable modules eliminating duplicate `scripts/lib/common.py` scripts across projects.

### REST Client HTTP Transport
- Provide a stdlib-only HTTP transport (`Transport` protocol, `UrllibTransport`, `RawResponse`,
  `TransportError`, `build_query_string`) in `support_python.net` for building REST API clients, with no third-party HTTP
  dependency.
- A non-2xx HTTP response is a completed round trip (`RawResponse`), not an exception; only a genuine
  connectivity failure (unreachable host, timeout, DNS failure) raises `TransportError`.
- Provide typed exception hierarchy mapping via `support_python.errors`.

### REST Client Error Hierarchy
- Provide a unified exception hierarchy (`ApiError`, `AuthenticationError`, `ForbiddenError`, `ConflictError`, `ValidationError`, `NotFoundError`, `RateLimitError`, `ServerError`) for REST API clients.
- Provide backward-compatible aliases (`ServiceError`, `HttpApiError`, `NetworkError`) for client parity.
- Provide regex-based not-found heuristics (`DEFAULT_NOT_FOUND_PATTERNS`, `is_not_found_message`) to classify 400 responses with missing-resource messages.
- Provide status-code-to-exception mapping helpers (`map_error`, `error_for_status`).

### View Capture Engine and Static Server
- Provide headless Chrome/Chromium automation (`ViewCaptureEngine`) with cross-platform browser discovery and configurable viewports in `support_python.capture`.
- Provide an embedded static HTTP server (`EmbeddedStaticServer`, `StaticServerManager`) in `support_python.httpd` supporting SPA fallback, custom route mounts, and pluggable mock API endpoints.
- Provide automated visual UI tour orchestration (`run_tour`) with SHA-256 integrity checks, duplicate frame detection, snapshot archiving, and markdown report generation.
- Provide a declarative CLI runner (`run_capture_cli`) allowing consuming webapps to replace hundreds of lines of boilerplate with declarative preset configurations.

### SQL Snapshot Anonymizer
- Provide streaming SQL tokenization and masking (`anonymize_sql_stream`, `anonymize_sql_string`) for database dumps in `support_python.sql`.
- Provide deterministic password hash computation matching service authentication standards (`get_standard_password_hash`).
- Provide cross-project user identity anonymization parity (`get_anonymized_user_info`).
- Provide built-in table transformers for the `auth` profile (`users`, `credentials`, `tokens`, `applications`) and the `counters` profile (`users`, `tokens`, `webhooks`).
- Support extensible custom table transformers and privilege statement filtering.

### Reusable DevOps Package and Service Managers
- Provide `support_python.devops` with `steps`, `services`, `release`, `projects`, and `cli` modules so consuming
  repositories keep only a thin `devops.py` in `scripts/` pinned via `scripts/requirements.txt`
  (see [ADR-0001-devops-scripts-toolkit-scope.md](adrs/ADR-0001-devops-scripts-toolkit-scope.md) and
  [ADR-0003-standalone-tools-and-reusable-devops.md](adrs/ADR-0003-standalone-tools-and-reusable-devops.md)).
- Provide `DevopsCli` with standard `lint`, `format`, `test`, `build`, `check`, `clean`, `versions`, `release`, and
  `deploy` actions, `PythonProject`/`GradleProject`/`NodeProject` build adapters, and opt-in `docker`, `db`, `server`,
  `mail`, and `client` service action groups.
- Provide reusable Docker engine and desktop lifecycle management (`LocalDockerManager`).
- Discover `cloud-sql-proxy` across `PATH`, `repo_root`, and fallback directories, failing cleanly when Docker is missing (`CloudSqlProxyManager`, `resolve_cloud_sql_proxy_bin`).
- Provide isolated local MySQL container lifecycle, schema initialization, and snapshot loading/anonymization (`LocalMySqlManager`).
- Provide Java application server lifecycle, background execution, and health status polling (`LocalServerManager`).
- Provide sample email template test dispatching (`LocalMailManager`) and live endpoint/deployment verification (`LocalVerifier`).

### Agent Files and Agent Digest
- Provide the standalone `agent-files` CLI tool supporting `list`, `sync`, `check`, `review`, `help`, and `version`,
  replacing `update-global-agent-files.py` from dev-guidelines.
- Support discovery and configuration of installed AI coding tools (Claude Code, Antigravity, Codex CLI) through a
  built-in, JSON-extensible tool registry (`support_python.agent_files_config`) reading `.agent-files.json`.
- Inject the guideline digest of a source repository into guarded blocks of tool-specific target files
  (`~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`, `~/.codex/AGENTS.md`) and sync its skills into each tool's skills folder,
  preserving developer-specific content outside the guarded block and creating backups prior to mutation.
- Provide the standalone `agent-digest` CLI tool deriving size-capped agent digests and mechanical 1:1 agent skills
  from human guideline documents (see [ADR-0002-modular-agent-skills-architecture.md](adrs/ADR-0002-modular-agent-skills-architecture.md)).

### Models and Wire Helpers
- Provide a `WireEnum` base class supporting kebab-case string conversion and case/underscore-insensitive deserialization.
- Provide immutable dataclass models for standard server endpoints (`ApiRoute`, `ApiInfo`, `ServerStatus`, `LogEntry`) with bidirectional wire dictionary mapping.

---

## Technical Requirements
- **Python Version**: `>=3.9` (see [pyproject.toml](../pyproject.toml)'s `requires-python`).
- **Build System**: `setuptools`, with a `src/` layout (`src/support_python`).
- **Testing**: `pytest`-compatible test suite under `tests/` (runnable via `python -m pytest`).
- **Linting**: `ruff` ([pyproject.toml](../pyproject.toml)'s `[tool.ruff]`, 132-character line length).
- **Dependencies**: As few third-party dependencies as possible; each one explicitly evaluated and justified
  (license, maintenance, uniqueness of functionality) per
  [general-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/general-guidelines.md).
- **Packaging**: Standard [pyproject.toml](../pyproject.toml)-driven build (`python -m build`) producing an sdist and wheel,
  attached as downloadable assets on GitHub Releases.
- **Code Standards**: 4-space indentation, UTF-8 encoding, LF line endings, US English, 132-character line
  length ([.editorconfig](../.editorconfig), `ruff`).
- **Versioning**: [Semantic Versioning](https://semver.org/); backward-incompatible changes get an explicit
  breaking-change note in [CHANGELOG.md](../CHANGELOG.md).
