---
id: T0013
owner: "@gemini"
session: antigravity-20261107-e9a10c
needs: []
branch: task/T0013-consolidate-the-harness-and-logging-into-support-python
worktree: .plan/work/T0013-consolidate-the-harness-and-logging-into-support-python
status: completed
started_at: "2026-11-07T16:22:41Z"
ended_at: "2026-11-07T16:33:28Z"
review: agent
preview: none
protocol: standard
size_status: approved
size_estimate: 8 files, 1126 lines
usage:
  worker: {turns: 6, duration_s: 2143.2, input: 1036514, output: 50096, cache_read: 22040268}
  review: {turns: 4, duration_s: 482.4, input: 68, output: 14138, cache_read: 1365500, cache_write: 136888}
work_duration: 3935.3
size_approved: 8 files, 1126 lines
size_approved_by: "@gpellicciotta"
size_approved_at: "2026-11-07T16:06:27Z"
review_status: approved
review_round: 2
reviewed_by: "@claude"
completion-commit: 37cd18665d5b0c5c2016247da704791415354400
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
- [x] **[Read]**      Diff the harness and tool_common copies in both repositories and list behavior differences.
- [x] **[Implement]** Author failing tests for the merged harness behavior and the backup subcommand.
- [x] **[Verify]**    Run the new tests and confirm they fail for the expected reasons.
- [x] **[Implement]** Merge harness and tool_common behavior into support_python.cli and support_python.logging.
- [x] **[Implement]** Copy the backup script into support_python.backup, fix imports, and register the subcommand.
- [x] **[Verify]**    Run the full test suite and ruff checks; confirm everything passes.
- [x] **[Doc]**       Update CHANGELOG.md and the docs index with the new modules.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.

- [2026-11-07] **[Read]**
  Diffed harness and tool_common copies against support_python.cli and support_python.logging.
  - Bare invocation prints help; flag-prefixed args do not trigger fallback.
  - Preserve empty lines in multi-line log messages and expose PROJECT_VERSION.

- [2026-11-07] **[Verify]**
  Confirmed red-phase test failures across test_cli, test_logging, and test_backup_git_repos before implementation.

- [2026-11-07] **[Implement]**
  Merged harness and logging behavior and added support_python.backup with support-python backup subcommand.

- [2026-11-07] **[Verify]**
  Verified pytest suite (527 passed, 3 skipped) and ruff check/format pass.
  - Files touched: 8.
  - Lines touched: 109.
  - Reopenings: 0.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md and docs/index.md for support_python.backup and harness consolidation.
  - Touched undeclared docs/index.md required by Step 7.

- [2026-11-07] **[Size]**
  Size approval requested by the work loop: 8 files, 1126 lines exceeds 3x the approved 7 files, 350 lines.

- [2026-11-07] **[Size]**
  Size approved by @gpellicciotta for 8 files, 1126 lines.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 rejected by @claude: The code content is sound, but the branch holds no deliverable: the work is stuck in an unfinished rebase with.
  - Findings: [review-findings-1.md](T0013-consolidate-the-harness-and-logging-into-support-python/review-findings-1.md).

- [2026-11-07] **[Implement]**
  Resolved Round 1 review findings by resolving CHANGELOG.md under v1.0.17-pre, moving stream reconfiguration into backup.main(), and completing the rebase.

- [2026-11-07] **[Verify]**
  Verified 538 passed tests and clean ruff checks on committed rebase tip f1da35d.
  - Files touched: 8.
  - Lines touched: 105.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 2 approved by @claude: All three Round 1 rework items are fixed.
  - Findings: [review-findings-2.md](T0013-consolidate-the-harness-and-logging-into-support-python/review-findings-2.md).

- [2026-11-07] **[Complete]**
  Task completed successfully.

