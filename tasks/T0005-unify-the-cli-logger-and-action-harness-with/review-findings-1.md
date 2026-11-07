---
task: T0005
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T15:03:35Z
reviewed_commit: "803fdef"
base_commit: "8cd1396"
branch: task/T0005-unify-the-cli-logger-and-action-harness-with
---
# Review Findings: Task T0005 (Round 1)

## Summary
The work covers the stated features: `ToolHarness` and `Action`, a fallback action, an exit-code table, startup and completion banners, log-level resolution, and the `ToolLogger`/`TeeLogger` aliases. The new unit and subprocess tests exist. I ran `pytest` (523 passed, 3 skipped), `ruff check` and `ruff format --check`; all are clean.

I reject it for one functional bug in the build-metadata version suffix. I also found undocumented behavior changes to the existing `CliLogger` and a weak test for the bug.

## Defects
1. **Build-metadata suffix reads the wrong repository.** `get_full_version()` in `src/support_python/cli.py` calls `resolve_build_metadata()` with no `cwd`. That function defaults to `Path.cwd()`, so the suffix comes from the git repo the user is standing in, not from the tool's own checkout.
   - Reproduction: a `ToolHarness("demo", "d", version="1.0.0")` script printed `demo v1.0.0+939fe5f` when run from an unrelated git repo whose HEAD is `939fe5f`.
   - The same script printed `demo v1.0.0` from a non-git directory.
   - Every banner, `--version` output and startup log line is affected. Installed tools would show a random hash or none.
   - Fix: resolve relative to the tool or package source location (for example the directory of the calling script or `support_python`'s own file), or accept an explicit `cwd`/repo path in `ToolHarness`.
2. **The test cannot catch defect 1.** The subprocess integration test only asserts `"subproc-demo v1.0.0"` as a substring. The unit test patches `resolve_build_metadata` entirely. No test checks that the hash comes from the intended repository.
3. **Behavior changes to the existing `CliLogger` and `format_log_message` are not recorded.** The task requires the existing public API to stay compatible. Changes to defaults:
   - Default timestamps changed from local time to UTC.
   - `format_log_message(for_file=False)` now emits the DEBUG indicator; before, it stripped everything except WARN and ERROR.
   - `CliLogger(log_level=...)` makes `debug()` write to stdout, where before it was file-only.
   - The `log()` default level changed from `None` to `"INFO"`.
   - `log()` now routes WARN and ERROR to stderr by default.

   CLAUDE.md requires breaking changes to be "called out explicitly in `CHANGELOG.md`". The single CHANGELOG line mentions none of them. Either keep the old behavior or document each change.
4. **Dead code.** `CliLogger._file` is never assigned a file handle, so the branch that writes through it and the flush logic in `close()` never run. Each write still reopens the file. Remove it or implement it.

## Process Gaps
- The Execution Log claims "keeping the existing public API compatible". Defect 3 contradicts that and the log does not mention it.
- The CHANGELOG entry lists additions only. It does not say that existing defaults changed.

## Required Rework
1. Fix the build-metadata resolution so it targets the tool's checkout, not the process working directory. Add a test that fails when the hash comes from the wrong repository. For example, run the demo CLI with the cwd set to a different git repo and assert the suffix is not that repo's hash.
2. Either restore the old `CliLogger` and `format_log_message` defaults listed in defect 3, or document each change in `CHANGELOG.md` as a breaking change. Add or adjust tests that pin the chosen behavior.
3. Remove the unused `_file` handle code, or implement it and cover it with a test.
4. Re-run `pytest`, `ruff check` and `ruff format --check`, then update the Execution Log.
