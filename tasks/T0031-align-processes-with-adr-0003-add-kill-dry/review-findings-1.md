---
task: T0031
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T01:26:07Z
reviewed_commit: "1e35067"
base_commit: "c348d76"
branch: task/T0031-align-processes-with-adr-0003-add-kill-dry
---
# Review Findings: Task T0031 (Round 1)

## Summary
The work meets all three goals and matches the technical spec and ADR-0003.
- `processes kill --dry-run` reports `Would kill PID {{pid}}` or `Would skip protected PID {{pid}}`, terminates nothing, and exits `0`.
- `list --format` accepts `text|json` (default `text`); `--format table` exits `2`.
- JSON mode sends log lines to `stderr`, so `stdout` holds one JSON document.
- `docs/tools/processes.md` exists; `README.md`, `docs/index.md`, and `CHANGELOG.md` (with a `**[breaking]**` note) are updated.

Verification I re-ran in the worktree at `1e35067`:
- `.venv/Scripts/ruff check .` and `ruff format --check .`: clean (129 files).
- `.venv/Scripts/python -m pytest -q`: 748 passed, 3 skipped, 81 subtests passed.
- `tests/tools/test_processes.py`: 8 passed, including the installed-binary dry-run integration test.
- Manual runs of the installed `.venv/Scripts/processes`:
  - `kill <bash-winpid> --dry-run` prints the protected-PID `WARN` and exits `0`.
  - `list --format table` prints the argparse error and exits `2`.
  - `list --format json` writes only `[]` to `stdout` (banner lines go to `stderr`), with or without `--verbose`.
  - `kill --help` and `help --verbose` show `--dry-run` and the new example.

The commit message follows the one-sentence, past-tense, no-trailer convention.

## Defects
None blocking. Non-blocking observations:
1. `JsonModeLogger` (`src/support_python/tools/processes.py`) is now the third copy of a JSON-mode stderr-routing logger.
   The others are `StderrRoutingLogger` in `agent_files.py` and `_JsonAwareLogger` in `lint_markdown.py`.
   All three build from the base logger's private `_explicit_level_set`.
   This is a good candidate to consolidate in `support_python.cli` or `support_python.logging` in a follow-up.
2. `report_kill_plan` copies the protection check from `safe_kill` rather than adding a `dry_run` option to `safe_kill`.
   The two code paths could drift apart later.
   `processes.os.getpid()` reaches `os` through the `processes` module, which is an unusual idiom.
3. The dry run reports `Would kill PID 99999999` for a PID that does not exist.
   A real kill of that PID warns `PID ... not found.` instead.
   The spec does not require detecting absent PIDs, so this is acceptable as delivered.
4. `docs/tools/processes.md` leaves out the `processes help` / `processes version` usage lines.
   The sibling `docs/tools/lint-markdown.md` includes them.
5. Observed but not introduced by this change: `processes list | head -5` on Windows Git Bash fails with `OSError: [Errno 22]` when the pipe closes.
   The `list` render path changed only by mapping the format value.

## Process Gaps
- The Execution Log records "Completion validation found 1 errors ... TF020" but has no entry saying how TF020 was fixed.
- The integration scenario uses `--force` for the real kill instead of the plain `processes kill <pid>` from the spec.
  This deviation is recorded as `**[Decided]**` with its reason (Windows `taskkill` without `/F`), so it is acceptable.

## Required Rework
None.
