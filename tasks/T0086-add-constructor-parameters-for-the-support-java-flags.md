---
id: T0086
owner: ~
needs: [T0084]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0086: Add constructor parameters for the support.java flags, commands, endpoints, and env-file names in the devops service managers

## Goals
The devops service managers hardcode support.java server conventions with no way to override them.
Add constructor parameters for each one, with today's values as defaults, so existing callers behave identically.
Cover the server's command-line flags, mail back end, start command, and static-directory variable.
Also cover the mail test command, the verifier's health endpoint, running status, and assets, and the snapshot env-file names.

## Task Execution Steps
- [ ] **[Read]**      Read services.py and devops-scripts.md, listing every hardcoded flag, command, endpoint, and file name.
- [ ] **[Implement]** Write failing tests for the defaults, each override, and the custom-endpoint verifier scenario.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Add the constructor parameters to the four managers, defaulting to today's values.
- [ ] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Document the new parameters in devops-scripts.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
