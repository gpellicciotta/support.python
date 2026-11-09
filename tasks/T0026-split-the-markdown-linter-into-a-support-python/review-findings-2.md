---
task: T0026
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-09T21:23:04Z
reviewed_commit: "e100006"
base_commit: "8450b1e"
branch: task/T0026-split-the-markdown-linter-into-a-support-python
---
# Review Findings: Task T0026 (Round 2)

## Summary
Approved.
The code is unchanged since round 1 (`e100006`), which round 1 already judged correct.
All four round-1 rework items are resolved.
The reviewer re-ran the new evidence, and it now matches real tool output.

Independently verified by the reviewer on `e100006`:
- The primary checkout is clean on `main` at `8450b1e`, so `C:\Dev-Projects\support.python\src` is valid pre-split code.
- The reviewer re-ran the pre-split command from `validation-proof.md` §4 (`python -I`, `main`'s `support_python.markdown_lint.main`).
  It exits 1 with the same 10 issues, byte-for-byte, as the recorded transcript; only the elapsed time differs.
- The reviewer re-ran the post-split `lint-markdown.exe check --offline docs README.md CHANGELOG.md`.
  It exits 1 with the same 10 issues and an identical transcript, apart from timing.
- The reviewer ran `lint-markdown.exe check --offline docs CLAUDE.md`: exit 0, "All 9 markdown files passed linting.", as recorded.
- §2 now shows `support_python-2.0.6rc0`, the correct PEP 440 normalization of `2.0.6-pre`.
  The installed `__editable__.support_python-2.0.6rc0.pth` and dist-info confirm it.
- Full suite: `698 passed, 3 skipped, 64 subtests passed` (exit 0). `ruff check .` and `ruff format --check .` pass (96 files).
- The console script maps `lint-markdown = "support_python.tools.lint_markdown:main"`.
- The engine imports neither `argparse` nor `support_python.cli`.
- No `markdown_lint` references remain outside the legacy-removal test and frozen CHANGELOG history.
- The Execution Log now contains the **[Decide]** entry for the `_validate_external_url` fallback change.
- The **[Verify]** entries now cite only captured evidence.

## Defects
None.

## Process Gaps
- `technical-spec.md` § Declared Files still omits `tests/test_console_scripts.py` and `tests/test_markdown_profiles.py`.
  The Execution Log records the deviation, so this is non-blocking.
- The editable install into the shared primary `.venv` now points at this worktree's `src`.
  `validation-proof.md` §2 notes this and gives the fix.
  After merge and worktree removal, run `pip install --no-deps -e .` from the primary checkout.
  Until then, the primary checkout's venv runs the task-branch code.

## Required Rework
None.
