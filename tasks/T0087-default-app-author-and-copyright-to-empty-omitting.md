---
id: T0087
owner: "@gemini"
session: antigravity-20261110-d2076b
needs: []
branch: task/T0087-default-app-author-and-copyright-to-empty-omitting
worktree: .plan/work/T0087-default-app-author-and-copyright-to-empty-omitting
status: completed
started_at: "2026-11-10T21:25:09Z"
ended_at: "2026-11-10T22:30:27Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 6, duration_s: 6942.4, input: 6049066, output: 291902, cache_read: 190382938}
  review: {turns: 2, duration_s: 754.0, input: 24, output: 3406, cache_read: 470772, cache_write: 68078}
work_duration: 3917.4
review_status: approved
review_round: 1
reviewed_by: "@claude"
completion-commit: 000b0722a8aee4466eee0b5ebbf42972ea11b9a9
---
# T0087: Default APP_AUTHOR and COPYRIGHT to empty, omitting the banner copyright when empty, while the bundled tools keep theirs

## Goals
`cli.APP_AUTHOR` defaults to the maintainer's name, so every consumer's banner credits the maintainer unless overridden.
Default `APP_AUTHOR` and `COPYRIGHT` to empty strings.
`ToolHarness` and view capture then print `{prog} v{version}` without a copyright suffix when the copyright is empty.
The five bundled tools and this repository's devops script keep their current banner through one shared constant.
`DevopsCli` gains a `copyright` argument so consumers can set their own banner.

## Task Execution Steps
- [x] **[Read]**      Read cli.py, capture.py, devops/cli.py, and every place that builds or asserts a banner.
- [x] **[Implement]** Write failing tests for the empty default banner, explicit copyrights, and bundled tool banners.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Empty the defaults, add `TOOLS_COPYRIGHT`, wire it into the tools, and add the `DevopsCli` argument.
- [x] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Update cli-harness-and-logging.md, migration-v2.md, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Verify]**
  Completion validation found 2 errors; pending fix turn 1 of 2.
  - TF018.
  - TF020.

- [2026-11-10] **[Read]**
  Inspected banner construction and assertions across CLI, capture, devops, and tools.

- [2026-11-10] **[Implement]**
  Authored failing tests for default empty banner and explicit copyright forwarding.

- [2026-11-10] **[Verify]**
  Verified expected test failures and recorded red-phase output in validation proof.

- [2026-11-10] **[Implement]**
  Defaulted APP_AUTHOR and COPYRIGHT to empty strings and wired TOOLS_COPYRIGHT.

- [2026-11-10] **[Verify]**
  Ran full devops check suite confirming 1239 passed tests, lint, and build.

- [2026-11-10] **[Doc]**
  Updated migration guide, harness tutorial, and changelog with breaking changes.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude: Goals met.
  - Findings: [review-findings-1.md](T0087-default-app-author-and-copyright-to-empty-omitting/review-findings-1.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

