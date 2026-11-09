---
task: T0027
round: 1
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-09T21:50:20Z
reviewed_commit: "a899e36"
base_commit: "5c9566c"
branch: task/T0027-rename-backup-git-repos-to-git-repository-backup
---
# Review Findings: Task T0027 (Round 1)

## Summary
Approved. Every goal and technical-spec item is met.
- `TOOL_NAME` is `git-repository-backup`; banners, usage, examples, and temp-dir prefixes follow it.
- `PASSWORD_CHECK_TEXT` correctly keeps `backup-git-repos`, so existing archives still verify.
- Config resolution order matches the spec: explicit, new, legacy with one `WARN`, then none.
- `list --format json` writes only the JSON array to stdout; banners still reach the log file.
- Invalid `--format` and a missing explicit config exit 2.
- The new doc, README section, docs index, and CHANGELOG entry are accurate.
- The version bump to `2.0.8-pre` follows the per-task pattern of earlier commits.

Reviewer verification on `a899e36`:
- `.venv/Scripts/python -m pytest -q`: 701 passed, 3 skipped, 64 subtests passed.
- `ruff check .` and `ruff format --check .`: clean.
- `lint-markdown check` on the four changed docs: no issues on changed lines; 11 pre-existing issues elsewhere.
- Ran the installed `git-repository-backup.exe list --format json` myself, with `HOME`/`USERPROFILE` set to a temp home holding only a legacy config.
  It exited 0, printed a parseable array on stdout, and wrote exactly one legacy `WARN` to stderr.
  Output stayed JSON-only with `--verbose`; text mode shows `Config file: ... (legacy)`.

## Defects
None blocking. Non-blocking notes:
- `BackupHarness.log_startup` and `log_completion` copy the base `ToolHarness` message formats for JSON mode.
  A later change to the base banner format would not reach JSON mode.
  A `to_stdout` parameter on the base methods would remove the duplication.
- `log_completion` imports `time` inside the method, and `run_console_script` imports `os` inside the function.
  Module-level imports are the project idiom.
- Long usage lists `--format text|json` under global options, but only `list` accepts it; `backup --format json` exits 2.
  The text says "output format for list", so this is acceptable.
- The spec said to mirror `processes list --format json`, but that command prints its banners on stdout and is not parseable.
  The implementation correctly followed the spec's main requirement (JSON-only stdout) instead.

## Process Gaps
- `tests/test_console_scripts.py` now sets `PYTHONPATH=src` for installed console scripts.
  It is needed because the shared venv's editable install points at the main checkout.
  Without it, the installed exe still prints `backup-git-repos v...` from the main checkout's code.
  The Execution Log records the undeclared file but not this reason.
  The change also means these tests run the worktree source through the installed entry point, not the installed package alone.
- `docs/devops.md` still lists the removed `backup-git-repos.py` and other wrapper scripts.
  This dates from T0024 and is outside this task's declared files; it should be a backlog follow-up.
- `processes list --format json` emits startup and completion banners on stdout, so its JSON is not parseable.
  This is a pre-existing defect in a sibling tool and should be a backlog follow-up.

## Required Rework
None.
