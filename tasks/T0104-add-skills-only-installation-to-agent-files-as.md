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

