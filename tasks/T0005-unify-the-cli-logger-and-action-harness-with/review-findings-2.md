---
task: T0005
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-07T15:24:18Z
reviewed_commit: "a7b3f13"
base_commit: "8cd1396"
branch: task/T0005-unify-the-cli-logger-and-action-harness-with
---
# Review Findings: Task T0005 (Round 2)

## Summary
All four round 1 rework items are resolved at `a7b3f13`.

- **Build metadata.** `resolve_build_metadata()` now defaults to the `support_python` package directory. `ToolHarness` resolves it from `repo_dir`, which defaults to the caller's script directory. It no longer reads the process cwd.
- **Test for the fix.** The subprocess integration test runs the demo CLI with its cwd set to an unrelated git repo. It asserts the unrelated hash is absent from `--version` and help output. A unit test also pins the default `cwd` of the git call.
- **CliLogger compatibility.** I diffed the new `CliLogger` and `format_log_message` against `8cd1396`. I found no remaining behavior change in the defaults:
  - Timestamps are local time.
  - `format_log_message(for_file=False)` strips DEBUG.
  - `debug()` writes to the file only.
  - `log()` defaults to no level.
  - WARN and ERROR go to stderr only through `warning()` and `error()`.

  `test_backward_compatible_defaults` pins these. The CHANGELOG needs no breaking-change note, because nothing breaks.
- **Dead code.** The unused `_file` handle is gone.

Checks I ran in the worktree with `PYTHONPATH` set to its `src`:
- `pytest`: 525 passed, 3 skipped.
- `ruff check .`: clean.
- `ruff format --check .`: 77 files already formatted.

The implementation covers every goal feature: registered actions with handlers, a fallback action, an exit-code table, startup and completion banners, log-level resolution, and the build-metadata version suffix. It also provides the `ToolLogger` and `TeeLogger` aliases. The Technical Specifications test list is covered by unit tests plus the subprocess integration test, which checks exit codes 0, 1 and 2.

## Defects
None blocking.

Non-blocking observations:
- `ToolHarness` infers the build-metadata repo from the caller's script directory. An installed tool in `site-packages` shows no suffix, unless that directory sits inside a git repo. This fits the stated design, so no change is needed.
- `format_utc_timestamp` is exported but unused by the logger. The logger keeps local-time file stamps for compatibility.

## Process Gaps
None. The Execution Log records the round 1 fixes, the verification, and the size note (998 lines against a 600-line estimate, under the 3x sign-off threshold).

## Required Rework
None.
