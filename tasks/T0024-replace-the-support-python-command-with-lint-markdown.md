---
id: T0024
owner: ~
needs: [T0023]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0024: Replace the support-python command with lint-markdown, agent-files, and git-repository-backup console scripts, and drop the wrapper scripts

## Goals
Remove the `support-python` console script, `src/support_python/__main__.py`, and the demo `greet` CLI from `support_python.cli`.
Register `lint-markdown`, `agent-files`, and `git-repository-backup` console scripts beside `processes`, at the current module paths.
Rename agent-files' `TOOL_NAME` from `update-global-agent-files` to `agent-files`.
Delete the checkout wrappers and duplicated helpers under `scripts/` listed in the technical spec, with their tests.
Document per-user and global installation of the tools in `README.md`.

## Task Execution Steps
- [ ] **[Read]**      Read cli.py main, the pyproject scripts table, the wrapper scripts, and every test using them.
- [ ] **[Implement]** Write tests/test_console_scripts.py covering entry points, banners, and the removed support-python command.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Update pyproject.toml, cli.py, package exports, and the agent-files TOOL_NAME; delete the listed files.
- [ ] **[Verify]**    Reinstall editable, run the full suite, and run each console script's version action.
- [ ] **[Doc]**       Update README.md, CHANGELOG.md, docs/requirements.md, docs/agent-files.md, and docs/markdown-lint.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The user confirmed tools run directly from the terminal, so the wrappers go.
