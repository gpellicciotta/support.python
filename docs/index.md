# Documentation Index

Overview of all documentation for the `support-python` project.

---

## Core Documentation

- [Requirements](requirements.md): High-level goals, functional scope, and technical requirements.
- [DevOps & Operations](devops.md): Environment prerequisites, development workflows, testing, and release
  process.
- [Git helpers](../README.md#git-repository-helpers): Query contracts, tri-state booleans, porcelain parsing, and runner configuration.
- [Locking](../README.md#locking): Lock base class, file lock, null lock, Redis lock, MySQL advisory lock, and backend factory.
- [Process helpers](../README.md#process-hierarchy-and-safe-termination): Process hierarchy, start-time lookup, liveness checks, termination, and safe kill.
- [File helpers](../README.md#atomic-text-file-helpers): Atomic UTF-8 text writes, Windows-safe file replacement retries, and retry-hardened file reads.
- [Markdown table helpers](../README.md#markdown-table-helpers): ANSI-aware Markdown table formatting, delimiter pipe splitting, and column alignment validation.
- [README](../README.md): Project overview, build, install, and usage.
- [CHANGELOG](../CHANGELOG.md): Versioned changes and release history.
- [PLAN](../PLAN.md): Task index by milestone.
- [LICENSE](../LICENSE.md): License terms (MIT).

---

## Architectural Decision Records

- [ADR-0001: Scope for a Shared DevOps-Scripts Toolkit](adrs/ADR-0001-devops-scripts-toolkit-scope.md): Why
  deploy and bootstrap scripts stay project-local while a pinned-dependency pattern shares narrow helpers.

---

## Guidelines

This project follows the cross-project
[dev-guidelines](https://github.com/gpellicciotta/dev-guidelines), in particular its
[general guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/general-guidelines.md),
[Python guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/python-guidelines.md),
and
[coordinating work guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/coordinating-work-guidelines.md).
