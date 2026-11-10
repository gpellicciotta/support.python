---
id: T0020
owner: "@gemini"
session: antigravity-20261110-92e0d7
needs: []
branch: task/T0020-generalize-agent-digest-to-take-markdown-paths-order
worktree: .plan/work/T0020-generalize-agent-digest-to-take-markdown-paths-order
status: active
started_at: "2026-11-10T00:04:03Z"
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
- [x] **[Read]**      Read the ported agent_digest module, its tests, and every dev-guidelines-specific constant.
- [x] **[Implement]** Write failing tests for path collection, index ordering, output options, and merged check.
- [x] **[Verify]**    Run the new tests and record the expected failures as red-phase proof.
- [x] **[Implement]** Implement path collection, front-matter index ordering, output options, and removal of hardcoded constants.
- [x] **[Implement]** Merge validate into check and align usage, exit codes, and logging with the guidelines.
- [x] **[Verify]**    Run the full suite and the dev-guidelines integration commands from the technical spec.
- [x] **[Doc]**       Write docs/tools/agent-digest.md and update README.md, docs/index.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided: validate takes paths and also checks freshness; outputs default to ./agent-digest.md and ./agent-skills.

- [2026-11-09] **[Decide]**
  User changed the decision on 2026-11-09: `check` replaces `validate`, matching the ADR-0003 verb convention.

- [2026-11-10] **[Verify]**
  Verified red-phase failures for path collection, index ordering, output options, link-base derivation, and merged check.

- [2026-11-10] **[Implement]**
  Generalized agent-digest to accept <PATH>... inputs, order by front-matter index, rewrite /skills/<name>/SKILL.md links, derive --link-base from Git origin, fold validate into check with --skill-index, and update agent-files and docs.
  - Files touched: 8.
  - Lines touched: 2059.
  - Reopenings: 0.

- [2026-11-10] **[Verify]**
  Verified 136 passed tests across test_agent_digest.py, test_agent_files.py, and test_console_scripts.py, ruff check/format clean, lint-markdown clean across docs, and zero-diff agent-digest check on dev-guidelines.

