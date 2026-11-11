---
task: T0074
round: 1
verdict: rejected
reviewer: "@claude-2"
reviewed_at: 2026-11-11T00:54:34Z
reviewed_commit: "86a5811"
base_commit: "110e892"
branch: task/T0074-add-format-text-json-to-processes-kill-reporting
---
# Review Findings: Task T0074 (Round 1)

## Summary
The implementation is clean and well tested: `safe_kill_report`, the dry-run outcomes, docs, and CHANGELOG are in place. The processes tests pass (41) and `ruff` is clean. One goal violation remains: in `json` mode the interactive confirmation can pollute `stdout`.

## Defects
- `run_kill` (src/support_python/tools/processes.py) calls `confirm_typed(summary, "kill", input_fn=input)` when `--yes` is absent and `stdin` is a TTY.
  `confirm_typed` (src/support_python/devops/release.py:225-228) writes the summary lines with `print()` to `stdout`, and `input()` writes the prompt there too.
  So `processes kill 123 --format json | jq .` emits the summary and prompt before the JSON array, which breaks the goal "one JSON document on `stdout`, all log lines on `stderr`".
- No test covers `--format json` combined with the interactive confirmation path.

## Process Gaps
- The `docs/tools/processes.md` claim "log messages go to `stderr`" is untrue for the confirmation summary and prompt in `json` mode.

## Required Rework
- In `json` mode, keep the confirmation summary and prompt off `stdout`.
  For example, route them to `stderr`, or require `--yes` with `--format json` and exit `2` otherwise, and document the choice.
- Add a test that runs `kill --format json` without `--yes` on a faked TTY and asserts `stdout` holds only the JSON document (or the chosen refusal).
