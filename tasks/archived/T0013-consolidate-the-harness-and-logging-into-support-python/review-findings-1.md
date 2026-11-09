---
task: T0013
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T16:26:00Z
reviewed_commit: "1e7e048"
base_commit: "1e7e048"
branch: task/T0013-consolidate-the-harness-and-logging-into-support-python
---
# Review Findings: Task T0013 (Round 1)

## Summary
The code content is sound, but the branch holds no deliverable: the work is stuck in an unfinished rebase with an unresolved conflict.

- `git log main..HEAD` is empty. `HEAD` equals `main` (`1e7e048`).
- The worktree is mid `git rebase` (`pick 34216e5`, "fix conflicts and then run git rebase --continue").
- `CHANGELOG.md` is `UU` and contains `<<<<<<<`/`=======`/`>>>>>>>` markers.
- All other changes are only staged, not committed.

Checks on the staged and working tree content:
- `python -m pytest tests -q`: 538 passed, 3 skipped.
- `ruff check .` and `ruff format --check .`: clean.
- `PYTHONPATH=src python -m support_python.cli backup help` runs the backup CLI.
- `support-python --help` lists the `backup` action.
- `backup.py` differs from `scripts/backup-git-repos.py` only in the two import lines.
- The `ToolHarness` fallback and bare-invocation behavior now matches `scripts/_harness.py`.
- `format_log_message` now preserves blank lines, with a test.

The goals are met in substance. A reviewer or merger cannot take the work from this branch as it stands.

## Defects
1. **Work not committed; rebase in progress.** Nothing exists on the task branch beyond `main`, and the rebase has not been continued. The commit `34216e5` that holds the work sits outside the branch tip.
2. **Unresolved conflict markers in `CHANGELOG.md` (lines 15-23).** HEAD side has `## v1.0.17-pre` with the T0009 and T0005 entries. The task side has `## v1.0.15-pre` with the T0013 entry. `pyproject.toml` says `1.0.17-pre`, so the T0013 entry must go under `## v1.0.17-pre` and the stale `v1.0.15-pre` heading must be dropped. Project convention requires the top heading to match `pyproject.toml` exactly.
3. **Import-time side effect in a library module.** `src/support_python/backup.py` reconfigures `sys.stdout` and `sys.stderr` at import. This was fine for a standalone script. As a package module it mutates global state for any importer, including the test suite. Wrap it in `main()` or use the shared `support_python.terminal` UTF-8 console setup. This is a minor point and does not block on its own.

## Process Gaps
1. The Execution Log claims "Updated CHANGELOG.md" and a passing suite, yet the changelog is conflicted and no commit exists on the branch. Resolve the conflict and commit before requesting review.
2. `README.md` does not mention `support-python backup`. `CLAUDE.md` says README drift counts as a bug. `docs/index.md` links the source file rather than a documentation section. `docs/devops.md:49` still describes only `backup-git-repos.py`. This is acceptable while the old script stays, but add the new subcommand there or note it.
3. The CLAUDE.md architecture list lacks a `backup.py` entry (minor).
4. The task file lists 8 files and 1126 lines against a 7 files, 350 lines estimate. The size approval is recorded, so no gap.

## Required Rework
1. Resolve `CHANGELOG.md`: keep a single `## v1.0.17-pre` section containing all entries, including the T0013 entry. Remove all conflict markers and the `v1.0.15-pre` heading.
2. Finish the rebase with `git add CHANGELOG.md && git rebase --continue`, so the work is a commit on the task branch. Use a past-tense one-sentence message with no attribution trailer, per the user's CLAUDE.md.
3. Re-run `python -m pytest tests -q` and `ruff check .` / `ruff format --check .` on the committed result.
4. Optional: move the stdout/stderr reconfigure out of import time in `backup.py`, and add `support-python backup` to the README and `docs/devops.md`.
