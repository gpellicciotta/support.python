---
id: T0018
owner: "@gemini"
session: antigravity-20261107-6733bb
needs: []
branch: task/T0018-implement-the-processes-cli-and-standalone-script-with
worktree: .plan/work/T0018-implement-the-processes-cli-and-standalone-script-with
status: active
started_at: "2026-11-07T15:52:13Z"
ended_at: —
review: agent
preview: none
protocol: standard
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
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, and docs/index.md.
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

