---
id: T0109
owner: "@codex"
session: codex-20261112-8c0b03
needs: []
branch: task/T0109-let-a-release-skip-the-github-release-and
worktree: .plan/work/T0109-let-a-release-skip-the-github-release-and
status: completed
started_at: "2026-11-11T23:31:04Z"
ended_at: "2026-11-11T23:36:25Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 518.4, input: 154770, output: 15802, cache_read: 2596096, cache_write: 0}
  review: {turns: 2, duration_s: 50.6, input: 24, output: 3094, cache_read: 425000, cache_write: 52308}
work_duration: 321.1
review_status: approved
review_round: 1
reviewed_by: "@claude"
completion-commit: 334d10b4e70b7e86fb9c35fc2f95b7a9c2b83e15
---
# T0109: Let a release skip the GitHub release and gh checks, and honor --skip-checks for project-owned releases

## Goals
Let a release skip the GitHub release and gh checks, and honor --skip-checks for project-owned releases.

## Task Execution Steps
- [x] **[Implement]** Author regression tests for release skip flags.
- [x] **[Verify]**    Confirm regression tests fail before implementation.
- [x] **[Implement]** Implement required changes for T0109.
- [x] **[Verify]**    Verify implementation with automated test suites.
- [x] **[Doc]**       Update documentation and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-11] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-12] **[Decided]**
  Added --skip-github-release and forwarded requested skip flags to project-owned releases. Gradle tasks receive skipChecks and skipGithubRelease properties.

- [2026-11-12] **[Verify]**
  Verified 118 affected tests and 17 subtests, Ruff, CLI help, Markdown lint, and task validation. Recorded evidence in validation-proof.md.
  - Files touched: 10.
  - Lines touched: 104.
  - Reopenings: 0.

- [2026-11-12] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-12] **[Implement]**
  Authored CLI forwarding, Gradle property, and temporary Git pipeline regression tests before changing production code.

- [2026-11-12] **[Verify]**
  Confirmed five regression failures before implementation: unsupported skip options, ignored project checks, and missing pipeline configuration.

- [2026-11-12] **[Doc]**
  Updated release usage, adapter contracts, and CHANGELOG.md. Completion validation now checks execution-log coverage before review.

- [2026-11-12] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-12] **[Review]**
  Round 1 approved by @claude: Work meets the goals.
  - Findings: [review-findings-1.md](T0109-let-a-release-skip-the-github-release-and/review-findings-1.md).

- [2026-11-12] **[Complete]**
  Task completed successfully.

