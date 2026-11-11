# Documentation Index

Overview of all documentation for the `support-python` project.

---

## Project Essentials
- [README](../README.md): Project overview, build, install, and usage.
- [CHANGELOG](../CHANGELOG.md): Versioned changes and release history.
- [LICENSE](../LICENSE.md): License terms (MIT).
- [DevOps & Operations](devops.md): Environment prerequisites, development workflows, testing, and release process.
- [Migrating to v2.0.0](migration-v2.md): v1.x to v2.0.0 mapping of commands, modules, verbs, options, config files, and library API, plus the devops entry script migration pattern.

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
- [General Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/general-guidelines.md)
- [Python Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/python-guidelines.md)
- [CLI Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md)
- [Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md)
- [Plan Task Usage Guidelines](https://github.com/gpellicciotta/plan/blob/main/src/plan/skills/plan-task-usage-guidelines/SKILL.md)

---

## Command-Line Tools
- [processes](tools/processes.md): Process hierarchy, filtered listing, start-time lookup, liveness checks, and ancestor-protected kills with `kill --dry-run`.
- [agent-digest](tools/agent-digest.md): Markdown digest and skill derivation, front-matter ordering, and budget checks.
- [agent-files](tools/agent-files.md): Global agent instructions, skills synchronization, `.agent-files.json` schema, and `ToolRegistry`.
- [lint-markdown](tools/lint-markdown.md): Markdown style and link linter, rule registry, JSON profiles, and rule plugins.
- [git-repository-backup](tools/git-repository-backup.md): Bare mirror and encrypted 7-Zip archive backup and restore.

---

## Library Tutorials
- [CLI harness and logging](tutorials/cli-harness-and-logging.md): `ToolHarness`, `Action`, build-metadata versions, `CliLogger` with 11-character severity padding and console/file teeing, table output, and token storage.
- [Script utilities](tutorials/script-utilities.md): UTF-8 console setup, project version lookup, port checks, env-file parsing, and password hashing.
- [REST clients](tutorials/rest-clients.md): Stdlib-only HTTP transport, REST error hierarchy and status mapping, wire datetimes, and metadata models.
- [DevOps scripts](tutorials/devops-scripts.md): Subprocess step runners, local service managers, release helpers, `ReleasePipeline`, `DevopsCli` project adapters, `deploy`, and service action groups.
- [Git helpers](tutorials/git-helpers.md): Query contracts, tri-state booleans, porcelain parsing, and runner configuration.
- [Files and locking](tutorials/files-and-locking.md): Atomic UTF-8 text writes, retrying replaces and reads, and file, null, Redis, and MySQL locks with a backend factory.
- [Process management](tutorials/process-management.md): Process hierarchy, descendants, open-path lookup, PID-reuse-safe liveness checks, and ancestor-protected termination.
- [Markdown tables and linting](tutorials/markdown.md): ANSI-aware table formatting and alignment checks, and the in-memory linter API.
- [Configuration](tutorials/configuration.md): Declaring settings, resolving them by the guideline precedence, and adding the standard `config` command group.
- [Durations and rate limiting](tutorials/durations-and-rate-limiting.md): Duration and ISO-8601 parsing, human-readable and relative epoch formatting, and `TaskRateLimiter`.
- [View capture](tutorials/view-capture.md): Headless-Chrome view capture, UI tours, the capture CLI, and the embedded static server.
- [SQL anonymizer](tutorials/sql-anonymizer.md): Streaming SQL dump anonymization driven by a required transformers map and a declarative column-rule builder.
