---
task: T0018
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T19:14:03Z
reviewed_commit: "fd9b89f"
base_commit: "fd9b89f"
branch: task/T0018-implement-the-processes-cli-and-standalone-script-with
---
# Review Findings: Task T0018 (Round 1)

## Summary
The feature code is sound, but the branch is not in a mergeable state. The worktree is stopped mid-rebase onto `fd9b89f` (main) with unresolved conflicts, and `HEAD` equals `main`.

- With `PYTHONPATH=src`, the full suite passes: 730 passed, 3 skipped.
- `scripts/processes.py list --cwd .` runs and returns the expected process row on Windows.
- `pytest` and `ruff` cannot run from the repo itself, because `pyproject.toml` is unparseable.
- The task file marks "Run pytest, ruff check, and ruff format --check until all pass" as done. That cannot hold for the delivered tree.

## Defects
1. **`pyproject.toml` has unresolved conflict markers.**
   - Lines 7-11 hold `<<<<<<< HEAD`, `=======`, and `>>>>>>> c76e98c`.
   - The file is invalid TOML. `ruff check .` fails with "Failed to parse pyproject.toml", and the package cannot be installed or built.
   - The version is ambiguous. The branch side has `1.0.18-pre` and main has `1.3.3-pre`. The correct resolution is above main's version, for example `1.3.4-pre`.
2. **`CHANGELOG.md` has unresolved conflict markers, lines 15-30.**
   - The branch entry is headed `## v1.0.18-pre`, a version regression against main's `v1.3.3-pre`.
   - Resolving it needs a new top heading above `v1.3.3-pre`. That heading must match `pyproject.toml` exactly.
   - A naive resolution would merge the entry into the wrong section or drop the `v1.3.3-pre` and `v1.3.0` entries.
3. **The work is not committed on the branch.**
   - `git log main..HEAD` is empty.
   - The staged changes sit inside an interrupted `git rebase` (the pick of `c76e98c`).
   - The branch ref still points at the old, pre-rebase commit `c76e98c`, which sits on an older base.
4. **`docs/devops.md:48` still lists `kill-processes.py`.**
   - The script was deleted in this task.
   - `CHANGELOG.md:59` mentions it only in a historical entry, which is fine.
   - The devops script table must be updated to `processes.py`.

## Process Gaps
- The Execution Log claims pytest, ruff check, and ruff format passed. The delivered tree cannot run them, so the verification evidence is stale or from a different base.
- The task doc step "Update CHANGELOG.md, README.md, and docs/index.md" omits `docs/devops.md`, which documents the removed script.
- Minor: `processes list --help` shows `-f, --force` ("force termination") among the `list` options. That flag only applies to `kill`.

## Required Rework
1. Resolve the conflicts in `pyproject.toml` and `CHANGELOG.md`.
   - Bump to a version above main's `1.3.3-pre`, for example `1.3.4-pre`.
   - Use the same version in the changelog top heading and `pyproject.toml`.
   - Keep main's `v1.3.3-pre` and `v1.3.0` entries intact.
   - Keep the `processes = "support_python.cli_processes:main"` script entry.
2. Finish the rebase (`git rebase --continue`) so the work is a commit on the task branch on top of main.
3. Update `docs/devops.md` to replace `kill-processes.py` with `processes.py`.
4. Re-run `python -m pytest`, `ruff check .`, and `ruff format --check .` from the repo root, using the project venv. All three must pass. Record the output in the task log.
5. Optional: hide `--force` from `list --help`.
