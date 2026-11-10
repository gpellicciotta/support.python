---
id: T0098
owner: "@gemini"
session: antigravity-20261110-089e87
needs: []
branch: task/T0098-make-toolharness-version-output-show-the-pre-suffix
worktree: .plan/work/T0098-make-toolharness-version-output-show-the-pre-suffix
status: active
started_at: "2026-11-10T20:34:52Z"
ended_at: —
review: none
preview: none
protocol: adhoc
---
# T0098: Make ToolHarness version output show the -pre suffix instead of the PEP 440 rc0 form from package metadata

## Goals
`ToolHarness` prints the version it receives, so consumers passing `importlib.metadata.version(...)` print the normalized `3.0.0rc0` instead of `3.0.0-pre`; template.python's `myproject --version` prints `v3.0.0rc0+0a59a6f`.
Make `ToolHarness` map a trailing `rc0` back to `-pre`, as `get_package_version` already does, so every consumer shows the `-pre` form the change management guidelines require.
Recommend `get_package_version` for consumer `__version__` values in the `ToolHarness` docstring and the CLI harness tutorial.

## Task Execution Steps
- [x] **[Implement]** Write the tests listed in the technical spec.
- [x] **[Verify]**    Run the new tests and capture the expected failures.
- [x] **[Implement]** Map a trailing rc0 to -pre in the ToolHarness version handling.
- [x] **[Verify]**    Run the fast suite and the completion check; record output in validation-proof.md.
- [x] **[Doc]**       Update the tutorial and docstring, and add a CHANGELOG.md entry.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Review lowered from agent to none by @<your name>: Very simple task..

- [2026-11-10] **[Implement]**
  Mapped trailing rc0 to -pre in ToolHarness version handling and updated docstring.

- [2026-11-10] **[Doc]**
  Recommended get_package_version in CLI tutorial and added changelog entry.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 4.
  - Lines touched: 69.
  - Reopenings: 0.

