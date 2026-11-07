---
task: T0004
round: 1
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-07T14:27:11Z
reviewed_commit: "0b022dc"
base_commit: "3d2ba87"
branch: task/T0004-add-duration-and-time-formatting-helpers
---
# Review Findings: Task T0004 (Round 1)

## Summary
Approved. `durations.py` adds the seven in-scope helpers, extracted from plan's `utils/dates.py`.

- Scope is correct. `extract_reset_time_from_text`, `extract_rate_limit_reset`, and `now_iso` are excluded.
- `dates.format_datetime` is not shadowed. A test asserts this.
- All seven symbols are re-exported from the package root and listed in `__all__`.
- CHANGELOG, README, CLAUDE.md, and docs/index.md are updated. The `pyproject.toml` version matches `v1.0.12-pre`.

Verification, run in the worktree with `pythonpath = ["src"]` so the worktree sources are used:
- `pytest`: 509 passed, 3 skipped. `tests/test_durations.py` alone: 6 passed.
- `ruff check .`: all checks passed.
- `ruff format --check .`: 75 files already formatted.

I compared the code with plan's source line by line. It is identical except for one intentional change (see Defects).

## Defects
None blocking.

Non-blocking observation: `parse_duration_to_seconds` adds `if "-" in s: return None`, which the plan source lacks.
- Compound strings with a minus sign, such as `"5m-3s"`, now return `None`. Plan's version silently returned 303.
- The docstring changes "zero/negative" to "negative" to match: a zero total is returned as `0.0`.
- This is a sensible hardening, covered by the `"-5"` tests.
- If plan's `utils/dates.py` is later replaced by an import from this library, plan's behavior changes slightly. That follow-up task should note it.

## Process Gaps
None. The task file shows tests authored first, with the initial ImportError recorded before implementation. The execution log records outcomes. The commit message follows the one-sentence, past-tense rule.

## Required Rework
None.
