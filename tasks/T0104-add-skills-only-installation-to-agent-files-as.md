---
id: T0104
owner: "@claude"
session: claude-20261111-e8b7f9
needs: []
branch: task/T0104-add-skills-only-installation-to-agent-files-as
worktree: .plan/work/T0104-add-skills-only-installation-to-agent-files-as
status: active
started_at: "2026-11-11T06:58:40Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 488.0, input: 100, output: 50638, cache_read: 4102148, cache_write: 201548}
work_duration: 256.9
---
# T0104: Add skills-only installation to agent-files, as a command mode and an importable function, matching plan's current skill installer

## Goals
Let plan depend on support.python to install its bundled skills, as `plan setup` does today.
Add `--skills-only` to `agent-files sync` and `check`: it installs skills, skips the guarded block, and never needs a digest.
Expose the same installation as an importable function returning structured per-skill results.
Match every behavior of plan's installer, listed in the technical specification.
Specifications: [technical-spec.md](T0104-add-skills-only-installation-to-agent-files-as/technical-spec.md).

## Task Execution Steps
- [x] **[Read]**      Read plan's skills.py and its setup and skills tests.
- [x] **[Implement]** Author failing tests for skills-only sync, check, and the library function.
- [x] **[Verify]**    Run the new tests and record their failure output.
- [x] **[Implement]** Add --skills-only and the importable installation function.
- [x] **[Verify]**    Run the affected tests and the integration scenario.
- [x] **[Doc]**       Update docs/tools/agent-files.md and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Implement]**
  Added --skills-only, install_skills_only, install_skills, retire_skills; SKILL.md-only copy matches plan's installer.
  - Files touched: 5.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read plan's skills.py installer and the existing agent-files skill sync.

- [2026-11-11] **[Implement]**
  Authored failing tests for the library functions and skills-only sync and check.

- [2026-11-11] **[Verify]**
  Failing tests recorded before implementation.
  - 16 failed, 1 passed.

- [2026-11-11] **[Verify]**
  Affected tests and integration scenario pass.
  - 1218 passed, 5 skipped.

- [2026-11-11] **[Doc]**
  Updated agent-files docs and CHANGELOG.md; size note: diff exceeds typical line due to tests and docs.

