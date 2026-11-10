---
task: T0028
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T22:10:53Z
reviewed_commit: "54b0133"
base_commit: "887e11a"
branch: task/T0028-make-toolharness-configure-utf-8-output-and-remove
---
# Review Findings: Task T0028 (Round 1)

## Summary
The core change is correct and well tested.
- `ToolHarness.run` calls `configure_utf8_output()` before parsing (`src/support_python/cli.py:314`).
- The per-tool `reconfigure` blocks and the explicit call in `tools/processes.py` are gone.
- `ToolLogger` and `TeeLogger` are removed from `support_python.logging`, `__all__`, and the package root.
- New tests cover call order, the alias removal, the source scan, and a cp1252-pipe subprocess check.
- `validation-proof.md` records red-phase proof.

Reviewer verification on `54b0133`:
- `ruff check .` passed; `ruff format --check .` reported 97 files already formatted.
- `PYTHONPATH=src python -m pytest -q`: 705 passed, 3 skipped, 64 subtests passed.
- Installed `processes`, `agent-files`, `lint-markdown`, and `git-repository-backup` `help` exit 0 when piped with `PYTHONIOENCODING=cp1252`.
- Bare `processes` with no arguments still prints help and exits 0.

Verdict: rejected. The mechanical sweep left fallout and documentation drift. The spec puts sweep fix-ups in this task's scope. The rework is small.

## Defects
1. **Duplicated prose left by the sweep.** `src/support_python/processes.py:377` now reads "a CliLogger, CliLogger, or standard logging.Logger". `src/support_python/processes.py:417` lists `` ``CliLogger`` `` twice in the `safe_kill` `logger` argument docs.
2. **Removed aliases still documented.** These docs still advertise the removed public API:
   - `CLAUDE.md:35` says "`CliLogger` (`ToolLogger`/`TeeLogger` aliases)".
   - `docs/index.md:12` says "Unified `CliLogger` (`ToolLogger`/`TeeLogger`)".
   `docs/index.md` is a mandatory doc, and project conventions treat doc drift as a bug.
3. **Sweep renamed a local subclass to shadow the library class.** `src/support_python/tools/agent_files.py:36` now defines `class CliLogger(_BaseCliLogger)`. This subclass routes WARN/ERROR to stderr, so it behaves differently from `support_python.logging.CliLogger`. One name now means two classes, which is confusing. Rename it to something that describes it, such as `StderrRoutingLogger`, and update `tests/tools/test_agent_files.py` to match.

## Process Gaps
- The declared files list 11 files, but the diff touches 15. These were not declared:
  - `src/support_python/processes.py`
  - `tests/tools/test_agent_files.py`
  - `tests/tools/test_git_repository_backup.py`
  - `tests/tools/test_lint_markdown.py`
  The Execution Log reports "Files touched: 11" and "Lines touched: 109". `git diff --stat` shows 15 files, 144 insertions, and 113 deletions.
- The spec asked for an integration test of the *installed* console scripts printing a non-ASCII character. `test_tools_help_and_non_ascii_output_under_cp1252_pipe` uses `python -c` with each module's `main` instead. `validation-proof.md` ran the installed executables' `help`, but without a non-ASCII check. This is an acceptable proxy, but it differs from the spec and the task file does not say so.

## Required Rework
1. Remove the duplicated `CliLogger` mentions in `src/support_python/processes.py:377` and `:417`.
2. Remove the `ToolLogger`/`TeeLogger` alias mentions from `CLAUDE.md:35` and `docs/index.md:12`.
3. Rename the `agent_files` local subclass at `src/support_python/tools/agent_files.py:36` so it no longer shadows `CliLogger`. Update its tests.
4. Record the extra touched files and the integration-test deviation in the task file. Re-run `ruff check .`, `ruff format --check .`, and the full pytest suite.
