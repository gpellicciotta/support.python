---
id: T0018
owner: "@gemini"
session: antigravity-20261107-6733bb
needs: []
branch: task/T0018-implement-the-processes-cli-and-standalone-script-with
worktree: .plan/work/T0018-implement-the-processes-cli-and-standalone-script-with
status: active
started_at: "2026-11-07T19:11:09Z"
ended_at: —
review: agent
preview: none
protocol: standard
size_status: approved
size_estimate: 11 files, 1358 lines
usage:
  worker: {turns: 6, duration_s: 4889.4, input: 1609668, output: 236320, cache_read: 27597268}
  review: {turns: 2, duration_s: 273.2, input: 40, output: 8480, cache_read: 810610, cache_write: 69198}
work_duration: 12252.4
size_approved: 11 files, 1358 lines
size_approved_by: "@gpellicciotta"
size_approved_at: "2026-11-07T17:43:31Z"
review_status: pending
review_round: 2
---
# T0018: Implement the processes CLI and standalone script with safe kill and filtered list commands

## Goals
Implement the `processes` CLI and standalone `scripts/processes.py` script providing `kill` and `list` subcommands using `support_python.processes`.
Provide cross-platform process listing with filters for working directory, open files, start time boundaries, and ancestor/descendant hierarchies using stdlib and ctypes only.
Expose both a standalone script and a console entry point in pyproject.toml, replacing `scripts/kill-processes.py`.

## Task Execution Steps
- [x] **[Read]**      Read existing processes.py and kill-processes.py implementation and CLI options.
- [x] **[Implement]** Author unit and integration tests for list filters and CLI commands in tests/test_processes_cli.py.
- [x] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [x] **[Implement]** Implement process filtering logic and CLI handlers in processes.py, cli_processes.py, and scripts/processes.py.
- [x] **[Implement]** Register console script entry point in pyproject.toml and remove obsolete kill-processes.py.
- [x] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [x] **[Doc]**       Update CHANGELOG.md, README.md, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-07] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-07] **[Read]**
  Read existing processes.py, kill-processes.py, and CLI options.

- [2026-11-07] **[Verify]**
  Authored test_processes_cli.py and verified TDD red-phase failure before implementation.

- [2026-11-07] **[Implement]**
  Implemented process filtering, cli_processes.py, scripts/processes.py, and pyproject.toml entry point, removing obsolete kill-processes.py.

- [2026-11-07] **[Size]**
  Size approval requested by the work loop: 11 files, 1358 lines exceeds 3x the approved 8 files, 400 lines.

- [2026-11-07] **[Size]**
  Size approved by @gpellicciotta for 11 files, 1358 lines.

- [2026-11-07] **[Verify]**
  Verified pytest, ruff check, ruff format --check, and standalone processes CLI execution.
  - Files touched: 11.
  - Lines touched: +738 / -620.
  - Reopenings: 0.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md, README.md, docs/index.md, and companion validation-proof.md.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 rejected by @claude: The feature code is sound, but the branch is not in a mergeable state.
  - Findings: [review-findings-1.md](T0018-implement-the-processes-cli-and-standalone-script-with/review-findings-1.md).

- [2026-11-07] **[Implement]**
  Resolved rebase conflicts in pyproject.toml and CHANGELOG.md (v1.3.4-pre), updated docs/devops.md, scoped --force to kill, and completed rebase onto main (5c21562).

- [2026-11-07] **[Verify]**
  Verified full suite (730 passed, 3 skipped, 64 subtests passed), ruff check, and ruff format --check using project venv.
  - Files touched: 12.
  - Lines touched: +739 / -621.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 2 requested (mode: agent).

