---
task: T0030
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-10T01:06:24Z
reviewed_commit: "53fda80"
base_commit: "19230d3"
branch: task/T0030-align-lint-markdown-with-adr-0003-drop-the
---
# Review Findings: Task T0030 (Round 1)

## Summary
Most goals are met, and the change is tidy and well tested.
- `--fix` is gone. `check --fix` and `fix --fix` exit 2 with an error indicator.
- `fix --dry-run` writes nothing, lists the planned fixes, and exits 0.
- `check --format json` prints one parseable object with the documented keys.
- `fix --format` and `check --dry-run` are rejected with exit 2.
- `.lint-markdown.json` is now the default name. A legacy-only `.markdown-lint.json` is honored with one WARN.
- Docs, README, and CHANGELOG (`**[breaking]**` entry) are updated.

Verification I ran myself on commit `53fda80`:
- `.venv/Scripts/python -m pytest -q`: 744 passed, 3 skipped, 81 subtests passed, exit 0.
- `ruff check .`: all checks passed. `ruff format --check .`: 128 files already formatted.
- CLI scenarios run against the worktree `src`:
  - `check --fix` exited 2.
  - `check --offline --format json docs` printed `{"files_checked": 10, "issues": []}` with empty stderr, exit 0.
  - With only a legacy config, both text and JSON modes warned and honored it.
  - A dry run left the file bytes unchanged.
  - JSON with violations exited 1 with only JSON on stdout.
- `lint-markdown check` on the three changed docs reports only issues in lines this task did not touch.

Rejected for one correctness defect in JSON mode (D1). The fix is small.

## Defects
- **D1 (blocking): JSON mode hides every WARN/ERROR on stderr, so unexpected failures produce no output.**
  - `_JsonAwareLogger.log` (`src/support_python/tools/lint_markdown.py:31-35`) sets both `to_stdout=False` and `to_stderr=False` for any leveled message.
  - The spec only requires stdout to carry nothing but the JSON document. It does not ask for stderr to be silenced.
  - Six call sites flip `logger.json_mode = False` by hand to get errors through (lines 103-113, 136, 145, 156, 181). Any path without a flip stays silent.
  - Reproduced: I patched `MarkdownLinter.lint_content` to raise `RuntimeError("boom")`, then ran `main(["check", "--offline", "--format", "json", <file>])`.
    It returned exit 1 with empty stdout and empty stderr.
    `ToolHarness.run`'s `Execution error during check: boom` and the `Finished ... failed` line were both swallowed.
  - The flips are also inconsistent. The flips before errors are never undone, so `Finished ... failed` reaches stderr after a missing-path error.
    After a run with violations it does not reach stderr.
  - T0029 already handles this differently: `StderrRoutingLogger` in `src/support_python/tools/agent_files.py:42-49` keeps WARN/ERROR on stderr in JSON mode and only suppresses stdout.
- **D2 (minor, non-blocking): a nearer legacy config is silently ignored when a farther directory has `.lint-markdown.json`.**
  - `_discover_config_path` searches every directory for the new name before it looks for any legacy file.
  - Reproduced with `p/pyproject.toml`, `p/.lint-markdown.json` (`disable: MD005`), and `p/sub/.markdown-lint.json` (`disable: MD001`), running `check --offline sub` from `p`:
    MD001 was reported and no legacy warning appeared.
  - Before this change, the nearest config won. The spec says "the new name wins", which can be read either way.
  - Silently ignoring a legacy file without a warning is still surprising during the v2.x migration.
- **D3 (minor, non-blocking): misleading test comment.**
  - `tests/test_markdown_profiles.py:247` was changed to say `.lint-markdown.json`.
  - `cfg_path` at line 239 is still `.markdown-lint.json`, so that block actually exercises the legacy fallback.
- **D4 (minor, non-blocking): the library reads legacy configs without any warning.**
  - `load_profile(directory)` and the CWD lookup in `src/support_python/markdown/profiles.py` fall back to `.markdown-lint.json` silently.
  - Only the CLI warns. Library callers get no deprecation signal before v3.0.0, for example a `warnings.warn(..., DeprecationWarning)`.

## Process Gaps
- The validation proof's "CLI Integration Verification" ran `python src/support_python/tools/lint_markdown.py` with `PYTHONPATH=src`.
  The spec asked for the installed `lint-markdown` console script.
  `TestEndToEnd.test_script_entry_point_json_output_and_legacy_config_warning` partly covers this, so it is a minor gap.
- No test covers JSON-mode error and diagnostic reporting on stderr, which is how D1 went unnoticed.

## Required Rework
1. Fix D1.
   - In JSON mode, suppress stdout only. Keep WARN/ERROR (including harness `Execution error` and `Finished ... failed` lines) on stderr, matching `StderrRoutingLogger` in agent-files.
   - Remove the manual `json_mode` toggles in `_discover_config_path` and `run_lint`.
2. Add a unit test for D1. With `--format json`, force an internal exception (or another error path) and assert:
   - stdout is empty or valid JSON;
   - stderr contains an `**[ERROR]**` line;
   - the exit code is non-zero.
3. Recommended, not required for approval:
   - D2: resolve per directory (nearest directory wins; within a directory, the new name wins), or at least warn when a legacy file is skipped.
   - D3: correct the comment.
   - D4: consider a `DeprecationWarning` in `load_profile`.
