---
id: T0015
owner: ~
needs: ['T0013']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
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
- [ ] **[Read]**      Read the script's repository-root constants and harness imports to plan the fixes.
- [ ] **[Implement]** Copy the script and its tests, then fix imports so the tests collect and fail.
- [ ] **[Verify]**    Confirm the ported tests fail only on the missing CLI registration.
- [ ] **[Implement]** Register the agent-files subcommand in support_python.cli.
- [ ] **[Verify]**    Run the full suite and a dry-run sync comparison against the original script.
- [ ] **[Doc]**       Update CHANGELOG.md and docs with the agent-files command.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.
