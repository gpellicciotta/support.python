---
id: T0025
owner: "@gemini"
session: antigravity-20261109-0a75f2
needs: []
branch: task/T0025-move-the-processes-agent-files-and-backup-cli
worktree: .plan/work/T0025-move-the-processes-agent-files-and-backup-cli
status: active
started_at: "2026-11-09T20:14:04Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 2964.8, input: 621292, output: 133632, cache_read: 22182396}
  review: {turns: 2, duration_s: 529.4, input: 72, output: 18578, cache_read: 2058826, cache_write: 119324}
review_status: pending
review_round: 2
work_duration: 1387.2
---
# T0025: Move the processes, agent-files, and backup CLI modules into the support_python.tools package without behavior changes

## Goals
Create the `support_python.tools` package and move the processes, agent-files, and backup CLI modules into it per the technical spec.
Move their tests into `tests/tools/` and `docs/agent-files.md` to `docs/tools/agent-files.md`.
Repoint console scripts, package re-exports, imports, mock patch targets, and links.
Change no behavior: existing tests must pass with only import and path fix-ups.

## Task Execution Steps
- [x] **[Read]**      Read the four modules' imports, the package root re-exports, and the tests' mock patch targets.
- [x] **[Implement]** Run the git mv commands listed in the technical spec.
- [x] **[Verify]**    Run the suite and record the resulting import failures as red-phase proof.
- [x] **[Implement]** Fix imports, patch targets, console script targets, re-exports, and links.
- [x] **[Verify]**    Reinstall editable, run the full suite, and run the integration commands from the technical spec.
- [x] **[Doc]**       Update README.md, docs/index.md, CLAUDE.md, and CHANGELOG.md for the new module paths.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Tool modules keep their own logic; only shared logic belongs in library modules.

- [2026-11-09] **[Read]**
  Inspected imports, lazy config imports, package re-exports, and test module paths across processes, agent-files, and backup modules.

- [2026-11-09] **[Implement]**
  Moved processes, agent-files, and backup CLI modules and tests into support_python.tools and tests/tools, and updated console script targets, imports, and re-exports. Also updated undeclared tests/test_console_scripts.py from T0024 (recount: 18 files, 129 lines).

- [2026-11-09] **[Doc]**
  Updated README.md, docs/index.md, docs/tools/agent-files.md, CLAUDE.md, and CHANGELOG.md (v2.0.4-pre) for the new support_python.tools module paths.

- [2026-11-09] **[Verify]**
  Captured red-phase import errors after git mv and verified full pytest suite (695 passed, task-159) and CLI entry points after editable reinstall.

- [2026-11-09] **[Verify]**
  Recorded task outcomes.
  - Files touched: 18.
  - Lines touched: 129.
  - Reopenings: 0.

- [2026-11-09] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-09] **[Review]**
  Round 1 rejected by @claude: The moves themselves are correct and complete.
  - Findings: [review-findings-1.md](T0025-move-the-processes-agent-files-and-backup-cli/review-findings-1.md).

- [2026-11-09] **[Decide]**
  Left src/support_python/__init__.py unchanged because main had no agent-files re-exports and importing support_python.tools.agent_files at package root added import-time filesystem side effects.

- [2026-11-09] **[Implement]**
  Removed package-root tool imports, updated CLAUDE.md and undeclared docs/requirements.md (recount: 18 files, 122 lines), and noted shared .venv editable install must be reinstalled from main after merge.

- [2026-11-09] **[Verify]**
  Verified post-rework test suite (695 passed, task-213), ruff check/format, lint-markdown, and CLI integration commands.

- [2026-11-09] **[Verify]**
  Recorded task outcomes.
  - Files touched: 18.
  - Lines touched: 122.
  - Reopenings: 0.

- [2026-11-09] **[Review]**
  Round 2 requested (mode: agent).

