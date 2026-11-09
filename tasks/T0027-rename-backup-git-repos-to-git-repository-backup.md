---
id: T0027
owner: "@gemini"
session: antigravity-20261109-2e56a8
needs: []
branch: task/T0027-rename-backup-git-repos-to-git-repository-backup
worktree: .plan/work/T0027-rename-backup-git-repos-to-git-repository-backup
status: active
started_at: "2026-11-09T21:25:57Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 2899.6, input: 587150, output: 92424, cache_read: 20595840}
review_status: pending
review_round: 1
---
# T0027: Rename backup-git-repos to git-repository-backup, read its legacy config with a warning, and add JSON list output

## Goals
Rename the backup tool's `TOOL_NAME` from `backup-git-repos` to `git-repository-backup`, covering banners, usage, and temporary-directory prefixes.
Read config from `~/.config/git-repository-backup/config.json`, falling back to `~/.config/backup-git-repos/config.json` with a warning.
Add `--format text|json` to the `list` action, and keep exit codes at 0, 1, and 2.
Write `docs/tools/git-repository-backup.md`.

## Task Execution Steps
- [x] **[Read]**      Read the backup tool's config loading, list output, and exit code paths.
- [x] **[Implement]** Write failing tests for the new name, both config paths, the warning, and JSON list output.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Rename TOOL_NAME, add the legacy config fallback, and add list --format.
- [x] **[Verify]**    Run the full suite and the installed integration command from the technical spec.
- [x] **[Doc]**       Write docs/tools/git-repository-backup.md, and update README.md, docs/index.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided on 2026-11-09: rename the tool to git-repository-backup and read ~/.config/backup-git-repos/ with a warning.

- [2026-11-09] **[Read]**
  Inspected config loading, list output, and exit code paths in git_repository_backup.py.

- [2026-11-09] **[Implement]**
  Added unit and integration tests for git-repository-backup naming, config fallback, and list --format json.

- [2026-11-09] **[Verify]**
  Confirmed red-phase failures (30 failed, 80 passed) on test_git_repository_backup.py.

- [2026-11-09] **[Implement]**
  Renamed TOOL_NAME to git-repository-backup, added legacy config fallback with warning, and implemented list --format text|json.

- [2026-11-09] **[Verify]**
  Verified full pytest suite (701 passed) and installed CLI legacy-config JSON list command.
  - Logged undeclared file tests/test_console_scripts.py for git-repository-backup banner check.

- [2026-11-09] **[Doc]**
  Wrote docs/tools/git-repository-backup.md and updated README.md, docs/index.md, and CHANGELOG.md.

- [2026-11-09] **[Verify]**
  Recorded task outcomes.
  - Files touched: 8.
  - Lines touched: 334.
  - Reopenings: 0.
  - Undeclared files: pyproject.toml, tests/test_console_scripts.py.

- [2026-11-09] **[Review]**
  Round 1 requested (mode: agent).

