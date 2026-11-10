---
task: T0030
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-10T01:14:22Z
reviewed_commit: "78f5723"
base_commit: "19230d3"
branch: task/T0030-align-lint-markdown-with-adr-0003-drop-the
---
# Review Findings: Task T0030 (Round 2)

## Summary
Approved. Commit `78f5723` resolves the blocking defect from round 1 and two of the three optional items.
- D1 fixed: `_JsonAwareLogger.log` now suppresses stdout only in JSON mode, so WARN and ERROR lines reach stderr.
- The six manual `json_mode` toggles are gone.
- D2 fixed: config lookup goes directory by directory, nearest first. Within one directory, the new name wins.
- D3 fixed: the test comment now says it covers the legacy file.
- A new unit test forces an internal exception under `--format json`. It asserts exit 1, empty stdout, and the stderr `Execution error` and `Finished ... failed` lines.

Verification I ran myself on commit `78f5723`:
- `python -m pytest -q`: 745 passed, 3 skipped, 81 subtests passed, exit 0.
- Targeted run of `tests/tools/test_lint_markdown.py` and `tests/test_markdown_profiles.py`: 45 passed.
- `ruff check .`: all checks passed. `ruff format --check .`: 128 files already formatted.
- Installed console script `.venv/Scripts/lint-markdown`, run with the worktree `src` first on `PYTHONPATH` (`version` reported `+78f5723`):
  - `check --offline --format json docs` printed `{"files_checked": 10, "issues": []}`, left stderr empty, and exited 0.
  - In a temp directory with only `.markdown-lint.json` disabling MD001, `check --offline .` warned once, honored the config, and exited 0.
- Module CLI scenarios:
  - JSON plus a legacy config: stdout held only JSON and stderr held the WARN. Exit 0.
  - JSON with violations: stdout parsed and listed all seven documented keys. Stderr held the WARN summary and `Finished ... failed`. Exit 1.
  - JSON with a missing path: stdout was empty and stderr held two ERROR lines. Exit 2.
  - `check --fix` and `fix --format json` exited 2 with an `**[ERROR]**` usage line.
  - `fix --dry-run` listed the planned MD005 fix and exited 0. The file's SHA-1 did not change.

## Defects
None blocking. The round-1 finding below is still open and was optional:
- **D4 (minor, non-blocking):** `load_profile` still reads a legacy `.markdown-lint.json` with no warning.
  - This happens in both the directory lookup and the CWD lookup, through `_resolve_dir_config_file` in `src/support_python/markdown/profiles.py`.
  - Only the CLI warns. Library callers get no deprecation signal before v3.0.0.

## Process Gaps
- The "CLI Integration Verification" section in `validation-proof.md` still runs `src/support_python/tools/lint_markdown.py` with `PYTHONPATH=src`. The spec asked for the installed `lint-markdown` console script.
  - I re-ran both integration commands through the installed script, and both passed. So this is a documentation gap only.

## Required Rework
None. Optional follow-up: add a `DeprecationWarning` for legacy config reads in `load_profile` (D4) before v3.0.0.
