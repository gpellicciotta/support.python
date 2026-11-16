---
id: T0112
owner: "@claude"
needs: []
branch: task/T0112-make-the-harness-version-action-reject-extra-arguments
worktree: .plan/work/T0112-make-the-harness-version-action-reject-extra-arguments
status: active
started_at: "2026-11-16T09:23:22Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0112: Make the harness version action reject extra arguments, suggesting versions when the tool has it

## Goals
`ToolHarness.run` answers `version` with the banner and exit 0, silently ignoring any further positional arguments.
So `devops.py version 3.4.0-pre` looks like it succeeded while it changed nothing; the intended action was `versions 3.4.0-pre`.
Make `version` with a positional argument fail with exit 2, an error naming the argument, and the usage line.
When the tool registers a `versions` action, the error also suggests `{{tool}} versions {{argument}}`.
Leading options that move after `version`, such as `--log-level DEBUG version`, keep working, option values included.

## Task Execution Steps
- [ ] **[Read]**      Read ToolHarness.run, _reorder_leading_options, and the version tests in tests/test_cli.py.
- [ ] **[Implement]** Author tests for rejected arguments, the versions hint, and kept leading options.
- [ ] **[Verify]**    Run tests/test_cli.py and capture the expected failures.
- [ ] **[Implement]** Reject positional arguments after version in ToolHarness.run, with the versions hint.
- [ ] **[Verify]**    Run tests/test_cli.py and tests/test_devops_cli.py, then the full test suite.
- [ ] **[Doc]**       Update the CLI harness tutorial and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-14] **[Doc]**
  Companion task file scaffolded at task creation.
