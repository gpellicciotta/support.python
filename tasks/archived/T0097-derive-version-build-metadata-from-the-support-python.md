---
id: T0097
owner: "@gemini"
session: antigravity-20261110-72c1f1
needs: []
branch: task/T0097-derive-version-build-metadata-from-the-support-python
worktree: .plan/work/T0097-derive-version-build-metadata-from-the-support-python
status: completed
started_at: "2026-11-10T20:48:29Z"
ended_at: "2026-11-10T21:24:49Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 3181.2, input: 2248104, output: 238964, cache_read: 46461386}
  review: {turns: 4, duration_s: 1065.4, input: 88, output: 17080, cache_read: 1747952, cache_write: 123372}
review_status: approved
review_round: 2
work_duration: 2179.7
reviewed_by: "@claude"
completion-commit: efef06e53d14de3ba40f523e4e634839263a7646
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
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Implement]**
  Derived version build metadata from support.python checkouts or install records.

- [2026-11-10] **[Verify]**
  Verified unit and integration test suite passing with foreign repository checks.

- [2026-11-10] **[Doc]**
  Documented build metadata derivation and recorded changelog entry.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude: The stated goal is met.
  - Findings: [review-findings-1.md](T0097-derive-version-build-metadata-from-the-support-python/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Addressed review round 1 rework preserving consumer repository build metadata.

- [2026-11-10] **[Verify]**
  Verified 36 tests passing including consumer and source checkout unit tests.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude: Round 1 rework is resolved.
  - Findings: [review-findings-2.md](T0097-derive-version-build-metadata-from-the-support-python/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

