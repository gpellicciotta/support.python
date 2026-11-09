---
id: T0020
owner: ~
needs: [T0019]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0020: Generalize agent-digest to take Markdown paths, order files by front-matter index, and fold validation into check

## Goals
Make `agent-digest` a generic tool that takes Markdown files and directories on the command line.
Order input files by an optional front-matter `index` key, then by command-line and path order.
Replace the dev-guidelines layout constants with `--digest` and `--skills-dir` options defaulting to `./agent-digest.md` and `./agent-skills`.
Fold validation into `check`, which takes the same paths as `generate`, and remove the `validate` action.
Make the CLI and logging comply with the `cli-guidelines` and `logging-guidelines` skills.
dev-guidelines will call `agent-digest generate <PATH>...` and `agent-digest check <PATH>...` with explicit output options.

## Task Execution Steps
- [ ] **[Read]**      Read the ported agent_digest module, its tests, and every dev-guidelines-specific constant.
- [ ] **[Implement]** Write failing tests for path collection, index ordering, output options, and merged check.
- [ ] **[Verify]**    Run the new tests and record the expected failures as red-phase proof.
- [ ] **[Implement]** Implement path collection, front-matter index ordering, output options, and removal of hardcoded constants.
- [ ] **[Implement]** Merge validate into check and align usage, exit codes, and logging with the guidelines.
- [ ] **[Verify]**    Run the full suite and the dev-guidelines integration commands from the technical spec.
- [ ] **[Doc]**       Write docs/tools/agent-digest.md and update README.md, docs/index.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided: validate takes paths and also checks freshness; outputs default to ./agent-digest.md and ./agent-skills.

- [2026-11-09] **[Decide]**
  User changed the decision on 2026-11-09: `check` replaces `validate`, matching the ADR-0003 verb convention.
