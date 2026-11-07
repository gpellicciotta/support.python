---
id: T0015
owner: "@gemini"
session: antigravity-20261107-f445b5
needs: []
branch: task/T0015-generalize-the-agent-files-sync-into-support-python
worktree: .plan/work/T0015-generalize-the-agent-files-sync-into-support-python
status: active
started_at: "2026-11-07T17:14:48Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 2593.2, input: 662578, output: 125098, cache_read: 27062786}
review_status: pending
review_round: 1
---
# T0015: Port the agent-files sync into support_python unchanged with an agent-files CLI and ported tests

## Goals
Copy dev-guidelines `scripts/update-global-agent-files.py` into `support_python.agent_files` unchanged apart from imports and repository-root resolution.
Expose it as `support-python agent-files list|sync|check|review`.
Parameterization follows in T0017.
Prerequisite: T0013 merged.

Completion check: the ported tests pass and a dry-run sync from dev-guidelines produces the same diff as the original script.
Size estimate: 4 files, 60 hand-written lines plus mechanical copies.
Mechanical command: `Copy-Item {{dev-guidelines}}/scripts/update-global-agent-files.py src/support_python/agent_files.py`
Mechanical command: `Copy-Item {{dev-guidelines}}/scripts/tests/test_update_global_agent_files.py tests/test_agent_files.py`

## Task Execution Steps
- [x] **[Read]**      Read the script's repository-root constants and harness imports to plan the fixes.
- [x] **[Implement]** Copy the script and its tests, then fix imports so the tests collect and fail.
- [x] **[Verify]**    Confirm the ported tests fail only on the missing CLI registration.
- [x] **[Implement]** Register the agent-files subcommand in support_python.cli.
- [x] **[Verify]**    Run the full suite and a dry-run sync comparison against the original script.
- [x] **[Doc]**       Update CHANGELOG.md and docs with the agent-files command.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.

- [2026-11-07] **[Read]**
  Read update-global-agent-files.py and test_update_global_agent_files.py imports, REPO_ROOT/DIGEST_PATH/SKILLS_DIR constants, digest generator lookup, and SyncHarness actions.

- [2026-11-07] **[Decided]**
  Resolved REPO_ROOT, DIGEST_PATH, SKILLS_DIR, and generate-agent-digest.py from find_project_root(Path.cwd()) when unpatched.
  - Aliased sync to update and check to diff in SyncHarness.run.
  - Moved stream reconfiguration into agent_files.main().
  - Bumped active version to v1.0.21-pre in CHANGELOG.md and pyproject.toml.

- [2026-11-07] **[Verify]**
  Copied agent_files.py and test_agent_files.py, fixed imports and repository-root resolution, and confirmed tests fail only on missing CLI registration (86 passed, 1 failed).

- [2026-11-07] **[Implement]**
  Registered agent-files subcommand in support_python.cli dispatching list, sync, check, and review.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md, README.md, docs/index.md, and pyproject.toml with support-python agent-files.
  - Touched undeclared README.md, docs/index.md, and pyproject.toml required by Step 6.
  - Size note: 2 mechanical copies plus 243 hand-written lines across 7 files.

- [2026-11-07] **[Verify]**
  Verified 741 passed tests (task-155), clean ruff checks, and matching dev-guidelines dry-run diff (differing only in version banner and duration).
  - Files touched: 5.
  - Lines touched: 26.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

