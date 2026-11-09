---
id: T0025
owner: ~
needs: [T0024]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0025: Move the processes, agent-files, and backup CLI modules into the support_python.tools package without behavior changes

## Goals
Create the `support_python.tools` package and move the processes, agent-files, and backup CLI modules into it per the technical spec.
Move their tests into `tests/tools/` and `docs/agent-files.md` to `docs/tools/agent-files.md`.
Repoint console scripts, package re-exports, imports, mock patch targets, and links.
Change no behavior: existing tests must pass with only import and path fix-ups.

## Task Execution Steps
- [ ] **[Read]**      Read the four modules' imports, the package root re-exports, and the tests' mock patch targets.
- [ ] **[Implement]** Run the git mv commands listed in the technical spec.
- [ ] **[Verify]**    Run the suite and record the resulting import failures as red-phase proof.
- [ ] **[Implement]** Fix imports, patch targets, console script targets, re-exports, and links.
- [ ] **[Verify]**    Reinstall editable, run the full suite, and run the integration commands from the technical spec.
- [ ] **[Doc]**       Update README.md, docs/index.md, CLAUDE.md, and CHANGELOG.md for the new module paths.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Tool modules keep their own logic; only shared logic belongs in library modules.
