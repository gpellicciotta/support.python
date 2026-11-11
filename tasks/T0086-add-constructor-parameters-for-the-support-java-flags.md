---
id: T0086
owner: "@claude"
session: claude-20261111-436207
needs: []
branch: task/T0086-add-constructor-parameters-for-the-support-java-flags
worktree: .plan/work/T0086-add-constructor-parameters-for-the-support-java-flags
status: active
started_at: "2026-11-11T00:31:15Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 844.8, input: 164, output: 66532, cache_read: 6758264, cache_write: 202782}
work_duration: 412.5
review_status: pending
review_round: 1
---
# T0086: Add constructor parameters for the support.java flags, commands, endpoints, and env-file names in the devops service managers

## Goals
The devops service managers hardcode support.java server conventions with no way to override them.
Add constructor parameters for each one, with today's values as defaults, so existing callers behave identically.
Cover the server's command-line flags, mail back end, start command, and static-directory variable.
Also cover the mail test command, the verifier's health endpoint, running status, and assets, and the snapshot env-file names.

## Task Execution Steps
- [x] **[Read]**      Read services.py and devops-scripts.md, listing every hardcoded flag, command, endpoint, and file name.
- [x] **[Implement]** Write failing tests for the defaults, each override, and the custom-endpoint verifier scenario.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Add the constructor parameters to the four managers, defaulting to today's values.
- [x] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Document the new parameters in devops-scripts.md and add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-11] **[Implement]**
  Added server, mail, verifier, and MySQL env-file constructor parameters with current defaults.
  - Files touched: 4.
  - Lines touched: 320.
  - Reopenings: 0.

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Listed hardcoded flags, commands, endpoints, and env-file names in services.py.

- [2026-11-11] **[Implement]**
  Wrote failing tests for defaults, overrides, and the custom-endpoint verifier scenario.

- [2026-11-11] **[Verify]**
  Recorded red-phase proof: 9 failed, 2 passed in validation-proof.md.

- [2026-11-11] **[Verify]**
  Ran devops check: exit 0, 1122 fast and 159 slow tests passed.

- [2026-11-11] **[Doc]**
  Documented parameters in devops-scripts.md and added a CHANGELOG.md entry.

- [2026-11-11] **[Review]**
  Round 1 requested (mode: agent).

