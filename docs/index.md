# Documentation Index

Overview of all documentation for the `support-python` project.

---

## Core Documentation
- [Requirements](requirements.md): High-level goals, functional scope, and technical requirements.
- [DevOps & Operations](devops.md): Environment prerequisites, development workflows, testing, and release
  process.
- [CLI harness and helpers](../README.md#shared-cli-helpers-tabular-output-and-session-storage): Action-oriented `ToolHarness`, `Action`, `build_action_parser`, version/help banners, and build-metadata version formatting.
- [CLI logging](../README.md#cli-logging): Unified `CliLogger` (`ToolLogger`/`TeeLogger`), `LogLevel`, `resolve_log_level`, 11-character severity padding, and console/file teeing.
- [Git repository backup](tools/git-repository-backup.md): Bare mirror and encrypted 7-Zip archive backup and restore exposed via `git-repository-backup` (see also [README](../README.md#git-repository-backup)).
- [Git helpers](../README.md#git-repository-helpers): Query contracts, tri-state booleans, porcelain parsing, and runner configuration.
- [Locking](../README.md#locking): Lock base class, file lock, null lock, Redis lock, MySQL advisory lock, and backend factory.
- [Process helpers and CLI](../README.md#process-hierarchy-and-safe-termination): Process hierarchy, filtered listing, start-time lookup, liveness checks, and ancestor-protected `processes` CLI.
- [File helpers](../README.md#atomic-text-file-helpers): Atomic UTF-8 text writes, Windows-safe file replacement retries, and retry-hardened file reads.
- [Markdown table helpers](../README.md#markdown-table-helpers): ANSI-aware Markdown table formatting, delimiter pipe splitting, and column alignment validation.
- [Markdown linter](tools/lint-markdown.md): Automated Markdown style and link linter, rule registry, and JSON profiles exposed via `lint-markdown` (see also [README](../README.md#markdown-linter)).
- [Agent files sync](tools/agent-files.md): Global agent instructions, skills synchronization, `agent-files.json` schema, and `ToolRegistry` exposed via `agent-files` (see also [README](../README.md#agent-files-sync)).
- [Duration and time helpers](../README.md#duration-and-time-formatting-helpers): Duration parsing, human-readable duration formatting, ISO-8601 and date parsing, and relative epoch formatting.
- [Task rate limiter](../README.md#task-rate-limiter): Sliding-window task dispatch rate limiting (`TaskRateLimiter`) with configurable window and wait-duration calculation.
- [DevOps script helpers and subprocess streaming](../README.md#devops-script-helpers-and-environment-managers): Subprocess line-by-line output streaming (`stream_subprocess`, `run_step_command`, `resolve_executable`), `run_step`, and local service managers.
- [README](../README.md): Project overview, build, install, and usage.
- [CHANGELOG](../CHANGELOG.md): Versioned changes and release history.
- `PLAN.md`: Task index by milestone (local plan store).
- [LICENSE](../LICENSE.md): License terms (MIT).

---

## Architectural Decision Records
- [ADR-0001: Scope for a Shared DevOps-Scripts Toolkit](adrs/ADR-0001-devops-scripts-toolkit-scope.md): Why
  bootstrap scripts and project-specific deploy steps stay project-local with a pinned `scripts/requirements.txt` dependency (partially superseded by [ADR-0003-standalone-tools-and-reusable-devops.md](adrs/ADR-0003-standalone-tools-and-reusable-devops.md)).
- [ADR-0002: Modular Guidelines and Mechanical Skill Derivation](adrs/ADR-0002-modular-agent-skills-architecture.md): Why
  guidelines carry skill front-matter and `agent-digest` derives a size-capped digest and on-demand skills from them.
- [ADR-0003: Standalone Tools and Reusable DevOps](adrs/ADR-0003-standalone-tools-and-reusable-devops.md): Why
  `support-python` ships five standalone console scripts (`processes`, `agent-files`, `agent-digest`, `lint-markdown`, `git-repository-backup`) with uniform CLI conventions and a library-based `support_python.devops` package.

---

## Guidelines
This project follows the cross-project
[dev-guidelines](https://github.com/gpellicciotta/dev-guidelines), in particular its
[general guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/general-guidelines.md),
[Python guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/python-guidelines.md),
and
[coordinating work guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/coordinating-work-guidelines.md).
