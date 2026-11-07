---
id: T0018
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
# T0018: Implement the processes CLI and standalone script with safe kill and filtered list commands

## Goals
Implement the `processes` CLI and standalone `scripts/processes.py` script providing `kill` and `list` subcommands using `support_python.processes`.
Provide cross-platform process listing with filters for working directory, open files, start time boundaries, and ancestor/descendant hierarchies using stdlib and ctypes only.
Expose both a standalone script and a console entry point in pyproject.toml, replacing `scripts/kill-processes.py`.

## Task Execution Steps
- [ ] **[Read]**      Read existing processes.py and kill-processes.py implementation and CLI options.
- [ ] **[Implement]** Author unit and integration tests for list filters and CLI commands in tests/test_processes_cli.py.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement process filtering logic and CLI handlers in processes.py, cli_processes.py, and scripts/processes.py.
- [ ] **[Implement]** Register console script entry point in pyproject.toml and remove obsolete kill-processes.py.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-07] **[Doc]**
  Companion task file scaffolded at task creation.
