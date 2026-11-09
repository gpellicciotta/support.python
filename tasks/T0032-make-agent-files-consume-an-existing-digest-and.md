---
id: T0032
owner: ~
needs: [T0020]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0032: Make agent-files consume an existing digest and skills directory instead of regenerating the digest itself

## Goals
Remove digest regeneration from agent-files: drop `get_digest_generator`, source freshness checks, and every generator call during `sync` or `check`.
Default `--digest` to `./agent-digest.md` and `--skills-dir` to `./agent-skills`, resolved against the project root or config directory.
Make `sync` and `check` exit 1 with a hint to run `agent-digest generate` when the digest is missing.
Keep explicit `--digest`, `--skills-dir`, and config keys working.

## Task Execution Steps
- [ ] **[Read]**      Read every agent-files use of the digest generator, digest sources, and default digest and skills paths.
- [ ] **[Implement]** Write failing tests for no generator calls, the new defaults, and the missing-digest hint.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Remove generator use and dev-guidelines path constants, and apply the new defaults.
- [ ] **[Verify]**    Run the full suite and the installed integration scenario from the technical spec.
- [ ] **[Doc]**       Update docs/tools/agent-files.md, README.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. Digest freshness becomes agent-digest check's job; agent-files only installs what it is given.
