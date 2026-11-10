---
id: T0089
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0089: Replace the stale update-global-agent-files.py text in the agent-files guarded block marker, still recognizing existing blocks

## Goals
The agent-files guarded block begin marker says `update-global-agent-files.py` generated it.
It also says to edit `guidelines/agent-digest.md` in dev-guidelines; neither the script nor that file exists any more.
Replace the default marker text with one naming `agent-files sync` and the source digest.
Existing global agent files carry the old marker, so sync must still find and replace their blocks.
Also stop agent_files.py from duplicating the marker and manifest constants of agent_files_config.py.

## Task Execution Steps
- [ ] **[Read]**      Read the marker handling in agent_files.py and agent_files_config.py, and the marker tests.
- [ ] **[Implement]** Write failing tests for legacy marker recognition, explicit markers, and constant deduplication.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Change the default marker text, add legacy begin recognition, and import the shared constants.
- [ ] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document the marker in agent-files.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
