---
task: T0018
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-07T19:27:42Z
reviewed_commit: "5c21562"
base_commit: "fd9b89f"
branch: task/T0018-implement-the-processes-cli-and-standalone-script-with
---
# Review Findings: Task T0018 (Round 2)

## Summary
Round 1 rework is complete. The work is one commit (`5c21562`) on top of main (`fd9b89f`) with no conflict markers.

- `pyproject.toml` and the `CHANGELOG.md` top heading both read `1.3.4-pre`. Main's older entries are intact.
- `docs/devops.md` now lists `processes.py`. The only remaining `kill-processes` mention is a historical changelog line.
- `--force` is scoped to `kill`. `list --help` no longer shows it.
- Full suite: 730 passed, 3 skipped, 64 subtests passed (PYTHONPATH=src, project venv).
- `ruff check .` passes. `ruff format --check .` reports 92 files already formatted.
- `scripts/processes.py list --descendants-of 4` and `list --started-after ... --format json` run and exit 0 on Windows.
- Goals and declared tests are met: filters, protected-PID kill, integration test, console entry point, removal of `kill-processes.py`.

## Defects
None blocking.

## Process Gaps
- Minor, non-blocking: the startup banner is written to stdout. `processes list --format json` output is therefore not pure JSON. Consider sending the banner to stderr in a follow-up.

## Required Rework
None.
