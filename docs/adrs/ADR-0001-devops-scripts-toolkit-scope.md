# ADR 0001: Scope for a Shared DevOps-Scripts Toolkit

## Status

**[Decided]** Accepted. `run_step` is implemented in `support_python.devops`.

## Context

Projects that consume this library each carry a handful of ops scripts: deploy to production, bootstrap a
development environment, start a Cloud SQL proxy, and verify a deployment. Comparing real copies of these
scripts showed how much they actually share:

- Proxy-start and verification scripts differ only in per-project constants such as instance name, port, and
  service-account path. They are good candidates for shared helpers.
- The bootstrap script must run on a bare checkout before `pip install`. A shared library it cannot yet have
  installed cannot help it, so it stays dependency-free.
- The deploy script diverges in real behavior: extra migration steps, different sets of built subprojects, and
  per-project image tags and service names. It is also the riskiest script to centralize.

## Decision

Do not build a single centralized "devops-scripts toolkit" that imports whole scripts. Instead:

- Consume `support_python` from ops scripts through a pinned `scripts/requirements.txt` git dependency, separate
  from each project's main build, so the primary app carries no ops-only dependencies.
- Extract only pieces with near-zero per-project divergence. `CliLogger` and `run_step` (a narrow
  subprocess-and-log helper) are the proof cases.
- Keep deploy and bootstrap scripts project-local. Their divergence is functional, so centralizing them would
  need config or plugin machinery that costs more than the copy-paste it replaces.

## Alternatives Considered

- Centralize all four scripts as importable modules. Rejected: it trades copy-paste for config-driven
  indirection without removing real complexity, and bootstrap cannot depend on an installed package.
- Do nothing. Rejected: duplicated logging and step-running code has a real maintenance cost.

## Consequences

- Positive: closes the duplication gap using a pattern that already works in production, at low risk.
- Positive: deploy-critical logic stays under each project's own review and release cycle.
- Negative: consumers must bump a pinned `support-python` version in `scripts/requirements.txt` themselves.
- Negative: deploy and bootstrap scripts keep diverging under copy-paste; structural changes must be applied to
  each project by hand.
