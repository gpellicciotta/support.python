# Requirements

Functional and technical requirements for the `support-python` project.

---

## High-Level Goals

- Provide a general-purpose Python support library and CLI, usable across Python projects, with
  as few third-party dependencies as possible so downstream consumers aren't burdened by transitive
  dependencies.
- Serve as the shared foundation for Python clients and standalone ops scripts that would otherwise each
  carry their own copy of the same helpers.
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

### CLI
- Provide a shared, reusable CLI helper (`build_action_parser`/`print_version`/`print_help`) for
  guideline-compliant, action-oriented CLIs: `-h`/`--help`, `-v`/`--version`, `--verbose`/`--debug`, the
  standard `{prog} v{version} - Copyright (c) {author}` header, and an exit-codes listing (`support_python.cli`).
- Provide tabular formatting (`format_table`) and structured output rendering (`render_output`, `json_serial`)
  supporting human-readable tables, dataclass lists, dictionaries, and JSON output formatting (`support_python.tables`).
- Provide pluggable session persistence (`TokenStore`, `FileTokenStore`) for CLI tools requiring multi-invocation
  state and session token retention under safe user directory paths (`support_python.tokens`).
- Provide a sample/demo CLI entry point (`support-python`, `greet`/`version`/`help` actions) exercising
  both the library and the shared CLI helper.

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

### DevOps Managers
- Provide reusable Docker engine and desktop lifecycle management (`LocalDockerManager`).
- Provide Cloud SQL Auth Proxy binary discovery and process launching (`CloudSqlProxyManager`, `resolve_cloud_sql_proxy_bin`).
- Provide isolated local MySQL container lifecycle, schema initialization, and snapshot loading/anonymization (`LocalMySqlManager`).
- Provide Java application server lifecycle, background execution, and health status polling (`LocalServerManager`).
- Provide sample email template test dispatching (`LocalMailManager`) and live endpoint/deployment verification (`LocalVerifier`).

### Models and Wire Helpers
- Provide a `WireEnum` base class supporting kebab-case string conversion and case/underscore-insensitive deserialization.
- Provide immutable dataclass models for standard server endpoints (`ApiRoute`, `ApiInfo`, `ServerStatus`, `LogEntry`) with bidirectional wire dictionary mapping.

---

## Technical Requirements

- **Python Version**: `>=3.9` (see `pyproject.toml`'s `requires-python`).
- **Build System**: `setuptools`, with a `src/` layout (`src/support_python`).
- **Testing**: `pytest`-compatible test suite under `tests/` (runnable via `python -m pytest`).
- **Linting**: `ruff` (`pyproject.toml`'s `[tool.ruff]`, 132-character line length).
- **Dependencies**: As few third-party dependencies as possible; each one explicitly evaluated and justified
  (license, maintenance, uniqueness of functionality) per
  [general-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/general-guidelines.md).
- **Packaging**: Standard `pyproject.toml`-driven build (`python -m build`) producing an sdist and wheel,
  attached as downloadable assets on GitHub Releases.
- **Code Standards**: 4-space indentation, UTF-8 encoding, LF line endings, US English, 132-character line
  length (`.editorconfig`, `ruff`).
- **Versioning**: [Semantic Versioning](https://semver.org/); backward-incompatible changes get an explicit
  breaking-change note in `CHANGELOG.md`.
