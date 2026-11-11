---
task: T0068
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-11T01:09:19Z
reviewed_commit: "28fcdb3"
base_commit: "0988d3b"
branch: task/T0068-move-git-repository-backup-settings-onto-the-shared
---
# Review Findings: Task T0068 (Round 1)

## Summary
The work meets every goal.
`git-repository-backup` now resolves settings through `SettingsSchema` and `resolve_settings`.
Precedence is options, `GIT_REPOSITORY_BACKUP_*`, user file, system file, default, with no project file.
The old and legacy user-file locations still work with their v3.0.0 warnings.
Unknown keys, malformed files, and invalid values warn once instead of exiting 2.
The `config` group is added through `add_config_actions` and targets the user file by default.

Verification run by the reviewer, using the main checkout's venv with `PYTHONPATH=src`:
- Fast suite: 1156 passed, 5 skipped.
- Backup, config-key, and config tests: 86 passed.
- `ruff check src tests`: clean.
- Manual run with `GIT_REPOSITORY_BACKUP_DEPTH=abc` and `GIT_REPOSITORY_BACKUP_ROOTS=a,b`: the bad depth warned and fell back to the default, roots came from the environment, and `config list` and `config path` worked.

I did not rerun the slow suite or markdown lint.
I relied on validation-proof.md for those: 58 slow tests passed, and 7 pre-existing lint issues sit only in the frozen fixtures.

## Defects
None.

Observation, not blocking: `config get NAME --source` fails with "expected one argument", because the harness's global `--source PATH` takes that flag.
The change skips registering the `get --source` flag in that case, and `get --verbose` prints the full card instead.
This is documented in git-repository-backup.md and recorded in the CHANGELOG as a library change.

## Process Gaps
None.
The worktree has no `.venv`, so `devops.py test` could not run there. I used the main venv instead.

## Required Rework
None.
