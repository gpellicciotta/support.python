---
id: T0013
owner: ~
needs: ['T0005']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0013: Consolidate the harness and logging into support_python and move backup-git-repos into the package

## Goals
Fold the newer behavior of `scripts/_harness.py` and `scripts/_tool_common.py`, and the dev-guidelines copies, into `support_python.cli` and `support_python.logging`.
Add `support_python.backup` as a copy of `scripts/backup-git-repos.py` with imports fixed, exposed as `support-python backup`.
The old scripts stay until dev-guidelines T0189 removes them.

Completion check: `python -m pytest tests -q` passes.
Size estimate: 7 files, 350 lines.
Mechanical command: `Copy-Item scripts/backup-git-repos.py src/support_python/backup.py`
Combined task: harness consolidation and the backup move share one import change; the backup module cannot use the old harness once removed.

## Task Execution Steps
- [ ] **[Read]**      Diff the harness and tool_common copies in both repositories and list behavior differences.
- [ ] **[Implement]** Author failing tests for the merged harness behavior and the backup subcommand.
- [ ] **[Verify]**    Run the new tests and confirm they fail for the expected reasons.
- [ ] **[Implement]** Merge harness and tool_common behavior into support_python.cli and support_python.logging.
- [ ] **[Implement]** Copy the backup script into support_python.backup, fix imports, and register the subcommand.
- [ ] **[Verify]**    Run the full test suite and ruff checks; confirm everything passes.
- [ ] **[Doc]**       Update CHANGELOG.md and the docs index with the new modules.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.
