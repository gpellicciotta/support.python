---
id: T0097
owner: "@gemini"
session: antigravity-20261110-72c1f1
needs: []
branch: task/T0097-derive-version-build-metadata-from-the-support-python
worktree: .plan/work/T0097-derive-version-build-metadata-from-the-support-python
status: active
started_at: "2026-11-10T20:48:29Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0097: Derive version build metadata from the support.python checkout, not an enclosing repository

## Goals
`resolve_build_metadata` in `src/support_python/cli.py` runs `git rev-parse` from the installed package directory.
Installed into a `.venv` inside another repository, it reports that repository's HEAD.
Seen in dev-guidelines: `agent-files version` printed `v2.0.0+0abd5e9`, the dev-guidelines commit.
Report build metadata only for an editable or source checkout of support.python itself.
Omit the suffix for installed wheels, or read the commit recorded at install time.
Completion check: a test installing into a venv inside a foreign Git repository shows no foreign hash.

## Task Execution Steps
- [x] **[Implement]** Implement required changes for T0097.
- [x] **[Verify]**    Verify implementation with automated test suites.
- [x] **[Doc]**       Update documentation and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Implement]**
  Derived version build metadata from support.python checkouts or install records.

- [2026-11-10] **[Verify]**
  Verified unit and integration test suite passing with foreign repository checks.

- [2026-11-10] **[Doc]**
  Documented build metadata derivation and recorded changelog entry.

