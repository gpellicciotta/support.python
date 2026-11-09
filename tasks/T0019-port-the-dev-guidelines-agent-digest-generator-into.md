---
id: T0019
owner: ~
needs: ['T0029']
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0019: Port the dev-guidelines agent digest generator unchanged into support_python.tools.agent_digest with an agent-digest console script

## Goals
Copy dev-guidelines `scripts/generate-agent-digest.py` into `support_python.tools.agent_digest` unchanged apart from imports, harness, and repository-root resolution.
Expose it as an `agent-digest` console script (`generate|check|validate`) that runs directly from the terminal after installation.
Make `tools.agent_files.get_digest_generator` use the packaged module instead of loading the script from the repository.
Take the sources from dev-guidelines commit `38e0de0`, because dev-guidelines deletes its copy.
Generalization follows in T0020.

## Task Execution Steps
- [ ] **[Read]**      Read the script, its tests, and agent_files digest loading at dev-guidelines commit 38e0de0.
- [ ] **[Implement]** Copy the script and tests, move real-repo tests onto fixtures, and fix imports.
- [ ] **[Verify]**    Confirm the ported tests fail only on the missing console script registration.
- [ ] **[Implement]** Register the agent-digest console script and packaged-module loading in tools.agent_files.
- [ ] **[Verify]**    Run the full suite and the dev-guidelines integration check at commit 38e0de0.
- [ ] **[Doc]**       Update CHANGELOG.md and README.md with the agent-digest command.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope drafted with the user: port unchanged first, then generalize in T0020, mirroring T0015 and T0017.

- [2026-11-09] **[Decide]**
  Retargeted to the v2.0.0 layout: no support-python action and no wrapper script; the tool lives in support_python.tools, per ADR-0003.
