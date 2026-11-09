---
task: T0024
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-09T20:10:49Z
reviewed_commit: "180ab88"
base_commit: "decca33"
branch: task/T0024-replace-the-support-python-command-with-lint-markdown
---
# Review Findings: Task T0024 (Round 2)

## Summary
Approved. Branch tip `180ab88` sits one commit on top of `main` (`decca33`), and the worktree is clean.
Every round-1 rework item is resolved:
- `docs/index.md` and `CLAUDE.md` now name `lint-markdown`, `agent-files`, and `git-repository-backup`; the demo-CLI line is gone.
- The `agent_files.py` digest hint reads `agent-files update`; the `tests/test_agent_files.py` docstring is fixed.
- `tests/test_console_scripts.py` resolves scripts via `sysconfig.get_path("scripts")`, and `tests/test_processes_cli.py` drops `resolve()`.
- The CHANGELOG entry sits under `## v2.0.2-pre`, and `pyproject.toml` stays at `2.0.2-pre`.
- `validation-proof.md` records the rebased run, and the Execution Log has a red-phase Verify entry.

I verified the work in a fresh temporary venv (`%TEMP%/t0024-r2-venv`), not the shared `.venv`:
- `pip install -e ".[dev]"` registers exactly `agent-files`, `git-repository-backup`, `lint-markdown`, and `processes`.
- Each tool's `version` action exits 0 with a `v2.0.2-pre+180ab88` banner (`backup-git-repos` banner kept per spec).
- `lint-markdown check --offline docs` exits 0 ("All 8 markdown files passed linting").
- `ruff check .` passes; `ruff format --check .` reports 91 files already formatted.
- `python -m pytest -q` gives 694 passed, 3 skipped, 64 subtests passed.

A repository-wide grep finds no live `support-python` subcommand, `python -m support_python`, or deleted-wrapper references.
The remaining `update-global-agent-files.py` strings are legacy marker text and requirement history, which T0029 owns.

## Defects
None blocking. Minor observations only:
1. `tests/test_processes_cli.py:151` hardcodes `Path(sys.executable).parent` plus `processes.exe`.
   It works in venvs and CI, but it duplicates `resolve_console_script` from `tests/test_console_scripts.py`.
2. `tests/test_console_scripts.py:119` asserts `"MD007" in stdout or "bad.md" in stdout`, so the rule ID itself is not pinned.
3. Running `lint-markdown` on `README.md` and `CHANGELOG.md` reports 5 issues; all are on lines this task did not change.
   Examples: `README.md:10` links the Git-ignored `PLAN.md`, and `CHANGELOG.md:34` links a `devops.py` that T0034 removed.

## Process Gaps
1. The released `v1.3.5` CHANGELOG entry was edited to turn links to deleted scripts into code spans.
   That keeps link checks green, but it rewrites a frozen entry. Acceptable here; mention it in the commit if it recurs.
2. The size estimate missed the undeclared test files and deletions. The work loop already flagged and approved this.

## Required Rework
None.
