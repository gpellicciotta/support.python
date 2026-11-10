---
task: T0036
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T02:27:50Z
reviewed_commit: "81f8e12"
base_commit: "0bbc7f9"
branch: task/T0036-add-a-dry-runnable-releasepipeline-that-freezes-tags
---
# Review Findings: Task T0036 (Round 1)

## Summary
Approved. `ReleasePipeline` and `confirm_typed` meet every goal and the spec flow.
The flow matches template.python's `release()` and adds a local-tag precondition.
All preconditions run before any change; dry run, confirmation, freeze skip, and step failure behave as specified.

Independent verification on `81f8e12`, using the main checkout's venv with `PYTHONPATH=src`:

```text
python -m pytest -q        -> 834 passed, 3 skipped, 81 subtests passed (exit 0)
ruff check --no-cache .    -> All checks passed!
ruff format --no-cache --check . -> 135 files already formatted
```

The suite includes the bare-origin integration scenario.
It stubs only `gh` and confirms the freeze commit, tag `v1.0.0`, notes and asset, and the `1.0.1-pre` reopen push.
The red-phase proof in `validation-proof.md` shows the expected `ImportError` before implementation.

## Defects
None blocking. Non-blocking observations:
- No precondition checks that local `main_branch` is level with `origin/<main_branch>` after the fetch.
  - If local is behind, `git push origin main` fails after the local freeze commit and tag exist.
  - The pipeline logs "Earlier steps were not rolled back", so the failure is visible.
  - template.python has the same gap, and the spec does not require the check.
- `capture_command` is a new public export, outside the spec API.
  - `test_devops.py` pins it, but the CHANGELOG entry does not name it.
- An already-frozen version keeps its `[YYYY-MM-DD]` status instead of `[released: ...]`. This matches the spec's freeze skip.
- `gh release view` treats any non-zero exit as "release absent", including network errors. This matches template.python.

## Process Gaps
None blocking. Minor notes:
- `tests/test_devops.py` was touched outside the declared files. The Execution Log records it.
- The `[Read]` and red-phase `[Verify]` log entries come after the outcome entries.
  - `validation-proof.md` still holds a credible red-phase record.
- Size: 680 lines against a 450-line estimate (about 1.5x), below the 3x sign-off line. The log records this.
- The worktree has no `.venv`, so the spec's `.venv/Scripts/python -m pytest -q` command does not run there as written.

## Required Rework
None.
