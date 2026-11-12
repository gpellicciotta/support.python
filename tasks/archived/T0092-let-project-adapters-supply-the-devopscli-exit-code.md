---
id: T0092
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T15:18:54Z"
ended_at: "2026-11-10T15:23:52Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-code-reviewer"
completion-commit: 426dc43bdd2d4482a93ef1e757f5f013c3658b02
---
# T0092: Let project adapters supply the DevopsCli exit-code text, dropping the virtual environment wording for Gradle and npm projects

## Goals
The T0091 review found that `DevopsCli` exit code 1 says "the virtual environment is missing" for every adapter.
**[Decided]** Reword the shared text to "a prerequisite is missing" instead of adding an adapter hook; it fits venvs, Gradle wrappers, and npm.
Completion check: `python scripts/devops.py check`.
Size estimate: 3 files, 10 lines

### Declared Files
- `src/support_python/devops/cli.py`
- `tests/test_devops_projects_gradle.py`
- `CHANGELOG.md`

### Tests
- Unit: Gradle help exit codes omit "virtual environment" and say "a prerequisite is missing".
- Integration test: none (help text only; the unit test renders the real help).

## Task Execution Steps
- [x] **[Implement]** Add a Gradle help test asserting adapter-neutral exit code text.
- [x] **[Verify]**    Run the test and record its failure output.
- [x] **[Implement]** Reword the exit code 1 text in `DevopsCli`.
- [x] **[Verify]**    Run `python scripts/devops.py check` and record the output.
- [x] **[Doc]**       Add the CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-reviewer.

- [2026-11-10] **[Implement]**
  Reworded DevopsCli exit code 1 to say a prerequisite is missing, after a failing Gradle help test.

- [2026-11-10] **[Verify]**
  Recorded the failing test and a green check with 1194 tests passing.

- [2026-11-10] **[Doc]**
  Added the CHANGELOG.md entry.

- [2026-11-10] **[Review]**
  Agent review approved; it confirmed the text fits all three adapters and found no stale quotes.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 3.
  - Lines touched: 8.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

