---
id: T0087
owner: "@gemini"
session: antigravity-20261110-d2076b
needs: []
branch: task/T0087-default-app-author-and-copyright-to-empty-omitting
worktree: .plan/work/T0087-default-app-author-and-copyright-to-empty-omitting
status: active
started_at: "2026-11-10T21:25:09Z"
ended_at: —
review: agent
preview: none
protocol: standard
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
- [ ] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Update cli-harness-and-logging.md, migration-v2.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
