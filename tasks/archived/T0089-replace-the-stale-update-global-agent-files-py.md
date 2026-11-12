---
id: T0089
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T13:05:36Z"
ended_at: "2026-11-10T14:32:16Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@giova"
completion-commit: 9f03dc9e4c71a8228532aca0e1fb4e975b80e51c
---
# T0089: Replace the stale update-global-agent-files.py text in the agent-files guarded block marker, still recognizing existing blocks

## Goals
The agent-files guarded block begin marker says `update-global-agent-files.py` generated it.
It also says to edit `guidelines/agent-digest.md` in dev-guidelines; neither the script nor that file exists any more.
Replace the default marker text with one naming `agent-files sync` and the source digest.
Existing global agent files carry the old marker, so sync must still find and replace their blocks.
Also stop agent_files.py from duplicating the marker and manifest constants of agent_files_config.py.

## Task Execution Steps
- [x] **[Read]**      Read the marker handling in agent_files.py and agent_files_config.py, and the marker tests.
- [x] **[Implement]** Write failing tests for legacy marker recognition, explicit markers, and constant deduplication.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Change the default marker text, add legacy begin recognition, and import the shared constants.
- [x] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the marker in agent-files.md and add a CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Implement]**
  Replaced the default begin marker text, added legacy begin-line recognition, and imported shared defaults from agent_files_config.py.

- [2026-11-10] **[Verify]**
  Recorded red, green, full check, and CLI dry-run evidence in validation-proof.md.
  - Files touched: 5.
  - Lines touched: 184.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  A separate claude-code subagent reviewed rounds 1 and 2 and reported APPROVE; round 2 fixed its BOM, word-extended marker, and earliest-match findings.

- [2026-11-10] **[Verify]**
  Recorded final outcomes after review fixes.
  - Files touched: 5.
  - Lines touched: 229.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 approved by @giova.

- [2026-11-10] **[Complete]**
  Task completed successfully.

