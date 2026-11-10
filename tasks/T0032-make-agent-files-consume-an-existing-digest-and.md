---
id: T0032
owner: "@claude"
session: claude-20261110-4207e1
needs: []
branch: task/T0032-make-agent-files-consume-an-existing-digest-and
worktree: .plan/work/T0032-make-agent-files-consume-an-existing-digest-and
status: active
started_at: "2026-11-10T01:28:46Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 1090.2, input: 184, output: 64274, cache_read: 9710632, cache_write: 261740}
work_duration: 557.4
---
# T0032: Make agent-files consume an existing digest and skills directory instead of regenerating the digest itself

## Goals
Remove digest regeneration from agent-files: drop `get_digest_generator`, source freshness checks, and every generator call during `sync` or `check`.
Default `--digest` to `./agent-digest.md` and `--skills-dir` to `./agent-skills`, resolved against the project root or config directory.
Make `sync` and `check` exit 1 with a hint to run `agent-digest generate` when the digest is missing.
Keep explicit `--digest`, `--skills-dir`, and config keys working.

## Task Execution Steps
- [x] **[Read]**      Read every agent-files use of the digest generator, digest sources, and default digest and skills paths.
- [x] **[Implement]** Write failing tests for no generator calls, the new defaults, and the missing-digest hint.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Remove generator use and dev-guidelines path constants, and apply the new defaults.
- [x] **[Verify]**    Run the full suite and the installed integration scenario from the technical spec.
- [x] **[Doc]**       Update docs/tools/agent-files.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Digest freshness becomes agent-digest check's job; agent-files only installs what it is given.

- [2026-11-10] **[Implement]**
  Removed digest generation from agent-files; sync and check now install the existing agent-digest.md and agent-skills, exiting 1 with an agent-digest generate hint.

- [2026-11-10] **[Verify]**
  Full suite, ruff, docs lint, and the installed integration scenario passed; proof in validation-proof.md.
  - 749 passed, 3 skipped.
  - Files touched: 6.
  - Lines touched: 381.
  - Reopenings: 0.

- [2026-11-10] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-10] **[Read]**
  Read agent-files digest generator use, stale-source checks, and the dev-guidelines digest and skills path defaults in agent_files.py and agent_files_config.py.

- [2026-11-10] **[Implement]**
  Authored failing tests for no generator import, agent-digest.md and agent-skills defaults, config-directory resolution, and the missing-digest hint.

- [2026-11-10] **[Verify]**
  Red phase: 13 agent-files tests failed before implementation; output recorded in validation-proof.md.

- [2026-11-10] **[Doc]**
  Updated docs/tools/agent-files.md, README.md, and CHANGELOG.md for the new defaults and the agent-digest generate prerequisite.

