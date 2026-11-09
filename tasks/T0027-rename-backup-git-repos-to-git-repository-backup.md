---
id: T0027
owner: ~
needs: [T0025]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0027: Rename backup-git-repos to git-repository-backup, read its legacy config with a warning, and add JSON list output

## Goals
Rename the backup tool's `TOOL_NAME` from `backup-git-repos` to `git-repository-backup`, covering banners, usage, and temporary-directory prefixes.
Read config from `~/.config/git-repository-backup/config.json`, falling back to `~/.config/backup-git-repos/config.json` with a warning.
Add `--format text|json` to the `list` action, and keep exit codes at 0, 1, and 2.
Write `docs/tools/git-repository-backup.md`.

## Task Execution Steps
- [ ] **[Read]**      Read the backup tool's config loading, list output, and exit code paths.
- [ ] **[Implement]** Write failing tests for the new name, both config paths, the warning, and JSON list output.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Rename TOOL_NAME, add the legacy config fallback, and add list --format.
- [ ] **[Verify]**    Run the full suite and the installed integration command from the technical spec.
- [ ] **[Doc]**       Write docs/tools/git-repository-backup.md, and update README.md, docs/index.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided on 2026-11-09: rename the tool to git-repository-backup and read ~/.config/backup-git-repos/ with a warning.
