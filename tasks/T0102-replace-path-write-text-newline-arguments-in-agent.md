---
id: T0102
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T17:12:03Z"
ended_at: "2026-11-10T17:18:45Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@codex"
completion-commit: 9a87805a8fb99e62654975a01cf0dd4ebf372baf
---
# T0102: Replace Path.write_text newline arguments in agent-digest, which Python 3.9 rejects, and guard src against them

## Goals
Replace the `Path.write_text(newline=...)` calls in `agent-digest`, which Python 3.9 rejects.
Guard `src/` with a test that fails on `newline` arguments to `Path.write_text` and `Path.read_text`.
Completion check: `python scripts/devops.py check`, then the GitHub Python 3.9 CI job
Size estimate: 3 files, 40 lines

### Declared Files
- src/support_python/tools/agent_digest.py
- tests/test_python39_compat.py
- CHANGELOG.md

### Tests
- Unit: an AST scan of `src/` finds no `write_text` or `read_text` call with a `newline` argument.
- Integration: the GitHub Python 3.9 job passes the agent-digest and agent-files suites.

## Task Execution Steps
- [x] **[Implement]** Author the AST guard test for `newline` arguments in `src/`.
- [x] **[Verify]**    Run it and record the failure, plus the Python 3.9 CI failures.
- [x] **[Implement]** Write digest and skill files through an LF `open` helper.
- [x] **[Verify]**    Run the local check and confirm the Python 3.9 CI job passes.
- [x] **[Doc]**       Add the CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @codex: No correctness bugs; CI run 42863145089 passed both jobs.

- [2026-11-10] **[Implement]**
  Wrote digest and skill files through an LF open helper instead of Path.write_text newline.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 3.
  - Lines touched: 43.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

