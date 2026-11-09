---
id: T0022
owner: ~
needs: []
branch: —
worktree: —
status: cancelled
started_at: —
ended_at: "2026-11-09T18:44:21Z"
review: agent
preview: none
protocol: standard
---
# T0022: Expose the agent-files sync as an installable agent-files console script

## Goals
Add an `agent-files = "support_python.agent_files:main"` entry under `[project.scripts]` in `pyproject.toml`.
After installing the package, `agent-files list|sync|check|review` must behave like `support-python agent-files ...`.
Rename `TOOL_NAME` in `support_python.agent_files` from `update-global-agent-files` to `agent-files`, so banners and usage match the command.
dev-guidelines documents `agent-files sync` and relies on this entry point.

## Task Execution Steps
- [ ] **[Implement]** Add tests for the agent-files entry point and the agent-files banner and usage name.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Add the console script entry, rename TOOL_NAME, and reinstall the package.
- [ ] **[Verify]**    Run the full suite and agent-files list from an installed environment.
- [ ] **[Doc]**       Document the agent-files command in docs/agent-files.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Requested by the user so dev-guidelines can document agent-files as a standalone command.

- [2026-11-09] **[Cancelled]**
  Superseded by T0024 and T0029, which install agent-files and align its verbs and tool name.

