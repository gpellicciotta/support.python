# Documentation Index

Overview of all documentation for the `support-python` project.

---

## Project Essentials
- [README](../README.md): Project overview, build, install, and usage.
- [CHANGELOG](../CHANGELOG.md): Versioned changes and release history.
- [LICENSE](../LICENSE.md): License terms (MIT).
- [DevOps & Operations](devops.md): Environment prerequisites, development workflows, testing, and release process.

---

## Requirements & Design
- [Requirements](requirements.md): High-level goals, functional scope, and technical requirements.
- [ADR-0001: Scope for a Shared DevOps-Scripts Toolkit](adrs/ADR-0001-devops-scripts-toolkit-scope.md): Why
  bootstrap scripts and project-specific deploy steps stay project-local with a pinned `scripts/requirements.txt` dependency (partially superseded by [ADR-0003-standalone-tools-and-reusable-devops.md](adrs/ADR-0003-standalone-tools-and-reusable-devops.md)).
- [ADR-0002: Modular Guidelines and Mechanical Skill Derivation](adrs/ADR-0002-modular-agent-skills-architecture.md): Why
  guidelines carry skill front-matter and `agent-digest` derives a size-capped digest and on-demand skills from them.
- [ADR-0003: Standalone Tools and Reusable DevOps](adrs/ADR-0003-standalone-tools-and-reusable-devops.md): Why
  `support-python` ships five standalone console scripts (`processes`, `agent-files`, `agent-digest`, `lint-markdown`, `git-repository-backup`) with uniform CLI conventions and a library-based `support_python.devops` package.

---

## Guidelines
This project follows the cross-project [dev-guidelines](https://github.com/gpellicciotta/dev-guidelines), in particular:
- [general guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/general-guidelines.md),
- [Python guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/python-guidelines.md), and
- [coordinating work guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/coordinating-work-guidelines.md).

---

## Core Documentation
- [CLI harness and helpers](tutorials/cli-harness-and-logging.md): Action-oriented `ToolHarness`, `Action`, version/help banners, and build-metadata version formatting.
- [CLI logging](tutorials/cli-harness-and-logging.md#cli-logging): Unified `CliLogger`, `LogLevel`, `resolve_log_level`, 11-character severity padding, and console/file teeing.
- [Git repository backup](tools/git-repository-backup.md): Bare mirror and encrypted 7-Zip archive backup and restore exposed via `git-repository-backup` (see also [README](../README.md#git-repository-backup)).
- [Git helpers](tutorials/git-helpers.md): Query contracts, tri-state booleans, porcelain parsing, and runner configuration.
- [Locking](tutorials/files-and-locking.md#locks): Lock base class, file lock, null lock, Redis lock, MySQL advisory lock, and backend factory.
- [Process helpers and CLI](tools/processes.md): Process hierarchy, filtered listing, start-time lookup, liveness checks, and ancestor-protected `processes` CLI with `kill --dry-run` (see also the [process management tutorial](tutorials/process-management.md)).
- [File helpers](tutorials/files-and-locking.md#atomic-text-files): Atomic UTF-8 text writes, Windows-safe file replacement retries, and retry-hardened file reads.
- [Markdown table helpers](tutorials/markdown.md#table-helpers): ANSI-aware Markdown table formatting, delimiter pipe splitting, and column alignment validation.
- [Markdown linter](tools/lint-markdown.md): Automated Markdown style and link linter, rule registry, and JSON profiles exposed via `lint-markdown` (see also the [Markdown tutorial](tutorials/markdown.md#linter)).
- [Agent files sync](tools/agent-files.md): Global agent instructions, skills synchronization, `.agent-files.json` schema, and `ToolRegistry` exposed via `agent-files` (see also [README](../README.md#agent-files-sync)).
- [Agent digest generator](tools/agent-digest.md): Markdown digest and skill derivation, front-matter ordering, and budget checks exposed via `agent-digest` (see also [README](../README.md#agent-digest-generator)).
- [Duration and time helpers](tutorials/durations-and-rate-limiting.md): Duration parsing, human-readable duration formatting, ISO-8601 and date parsing, and relative epoch formatting.
- [Task rate limiter](tutorials/durations-and-rate-limiting.md#task-rate-limiter): Sliding-window task dispatch rate limiting (`TaskRateLimiter`) with configurable window and wait-duration calculation.
- [Script utilities tutorial](tutorials/script-utilities.md): UTF-8 console setup, project version lookup, port checks, env-file parsing, and password hashing.
- [REST clients tutorial](tutorials/rest-clients.md): Stdlib-only HTTP transport, REST error hierarchy and status mapping, wire datetimes, and metadata models.
- [View capture tutorial](tutorials/view-capture.md): Headless-Chrome view capture, UI tours, the capture CLI, and the embedded static server.
- [SQL anonymizer tutorial](tutorials/sql-anonymizer.md): Streaming, deterministic anonymization of `auth` and `counters` SQL dumps.
- [DevOps scripts tutorial](tutorials/devops-scripts.md): Subprocess step runners, local service managers, release helpers, `ReleasePipeline`, `DevopsCli` project adapters, `deploy`, and service action groups.
- [Migrating to v2.0.0](migration-v2.md): v1.x to v2.0.0 mapping of commands, modules, verbs, options, config files, and library API, plus the devops entry script migration pattern.



