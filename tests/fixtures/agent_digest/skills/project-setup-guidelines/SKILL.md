---
name: project-setup-guidelines
description: >-
  Standards for repository structure, standard project files, documentation
  hierarchy, bootstrap commands, and third-party dependencies. Use when
  bootstrapping a new repository, adding dependencies, or organizing
  documentation.
---

# Project Setup Guidelines
Standards for repository layout, core documentation files, environment bootstrapping, and dependency evaluation.

## Standard Repository Files and Layout
- Place core project files in the repository root directory:
  - `README.md`: project overview and links to documentation.
  - `LICENSE.md`: software license governing the project.
  - `CHANGELOG.md`: human-readable change history grouped by semantic version.
  - `PLAN.md`: authoritative task index across free-form sections.
  - `.plan/`: workspace directory holding tasks, protocols, and sessions.
- Maintain mandatory documentation files under `docs/`:
  - `docs/index.md`: documentation index linking all guide documents.
  - `docs/requirements.md`: high-level functional and technical requirements.
  - `docs/devops.md`: build, test, deployment, and operational procedures.
- Maintain specialized project documentation under standard subdirectories:
  - `docs/specs/`: interface, format, and protocol specifications.
  - `docs/adrs/`: architectural decision records explaining key choices.
  - `docs/issues/`: root cause analysis and resolution records for complex bugs.
- Follow standard naming conventions for specialized documentation files:
  - Name architectural decision records as `docs/adrs/ADR-{{nnnn}}-{{slug}}.md` with a monotonic 4-digit zero-padded number.
  - Name interface, data, and protocol specifications as `docs/specs/{{slug}}.md` using descriptive lowercase kebab-case.
  - Name root cause analysis records as `docs/issues/RCA-{{issue-id}}-{{slug}}.md` or `docs/issues/RCA-{{yyyy-mm-dd}}-{{slug}}.md`.
- Keep documentation, indexes, requirements, and operations guides synchronized with actual code behavior.

- Maintain a `scripts/` directory holding `bootstrap-dev-environment.py` and `devops.py` scripts:
  - The `bootstrap-dev-environment.py` must have no external dependencies and set up a fully functional development environment.
  - The `devops.py` script provides access to all typical operations and procedures in the project.
- Prefer cross-platform Python scripts over PowerShell or Bash.

## Third-Party Dependencies
- Minimize third-party dependencies in direct and transitive project configurations.
- Evaluate licensing, maintenance status, necessity, and security before adding dependencies.
- Avoid duplicate dependency declarations across configuration manifests within the same project.
- Ensure production code remains usable independently of proprietary development tools.

## Code Cleanliness and Forwarding
- Use forwarding and re-export shims only as temporary steps during incremental migrations.
- Complete migrations by eliminating forwarding shims and consuming upstream APIs directly.
- Ensure production code remains clean and readable without unnecessary indirection layers.
