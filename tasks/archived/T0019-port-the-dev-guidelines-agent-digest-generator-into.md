---
id: T0019
owner: "@gemini"
session: antigravity-20261110-615440
needs: []
branch: task/T0019-port-the-dev-guidelines-agent-digest-generator-into
worktree: .plan/work/T0019-port-the-dev-guidelines-agent-digest-generator-into
status: completed
started_at: "2026-11-09T23:24:25Z"
ended_at: "2026-11-10T00:03:43Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 3859.6, input: 848046, output: 198448, cache_read: 18152008}
  review: {turns: 4, duration_s: 750.0, input: 76, output: 23142, cache_read: 2104452, cache_write: 113084}
review_status: approved
review_round: 2
work_duration: 2357.9
reviewed_by: "@claude"
completion-commit: 2e7ca3975bd6685ca3acc31713acedd86d2cb06f
---
# T0019: Port the dev-guidelines agent digest generator unchanged into support_python.tools.agent_digest with an agent-digest console script

## Goals
Copy dev-guidelines `scripts/generate-agent-digest.py` into `support_python.tools.agent_digest` unchanged apart from imports, harness, and repository-root resolution.
Expose it as an `agent-digest` console script (`generate|check|validate`) that runs directly from the terminal after installation.
Make `tools.agent_files.get_digest_generator` use the packaged module instead of loading the script from the repository.
Take the sources from dev-guidelines commit `38e0de0`, because dev-guidelines deletes its copy.
Generalization follows in T0020.

## Task Execution Steps
- [x] **[Read]**      Read the script, its tests, and agent_files digest loading at dev-guidelines commit 38e0de0.
- [x] **[Implement]** Copy the script and tests, move real-repo tests onto fixtures, and fix imports.
- [x] **[Verify]**    Confirm the ported tests fail only on the missing console script registration.
- [x] **[Implement]** Register the agent-digest console script and packaged-module loading in tools.agent_files.
- [x] **[Verify]**    Run the full suite and the dev-guidelines integration check at commit 38e0de0.
- [x] **[Doc]**       Update CHANGELOG.md and README.md with the agent-digest command.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope drafted with the user: port unchanged first, then generalize in T0020, mirroring T0015 and T0017.

- [2026-11-09] **[Decide]**
  Retargeted to the v2.0.0 layout: no support-python action and no wrapper script; the tool lives in support_python.tools, per ADR-0003.

- [2026-11-10] **[Read]**
  Read generate-agent-digest.py, test_generate_agent_digest.py, and agent_files digest loading at dev-guidelines commit 38e0de0.

- [2026-11-10] **[Implement]**
  Copied generate-agent-digest.py and tests from dev-guidelines 38e0de0 into agent_digest.py and test_agent_digest.py, moved real-repo tests onto fixtures, and updated imports.

- [2026-11-10] **[Verify]**
  Confirmed ported tests in test_agent_digest.py pass 37 in-process cases and fail only on the 4 end-to-end console script checks.

- [2026-11-10] **[Implement]**
  Registered the agent-digest console script in pyproject.toml and wired tools.agent_files.get_digest_generator to import support_python.tools.agent_digest.

- [2026-11-10] **[Doc]**
  Updated README.md and CHANGELOG.md (v2.0.13-pre) with the agent-digest command.

- [2026-11-10] **[Verify]**
  Verified 753 passed tests (task-118), clean ruff checks, and dev-guidelines 38e0de0 integration check (check, validate, and generate).
  - Files touched: 6.
  - Lines touched: 115.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude: Rejected.
  - Findings: [review-findings-1.md](T0019-port-the-dev-guidelines-agent-digest-generator-into/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Addressed round 1 review findings: bound generator.REPO_ROOT to _resolve_repo_root() in ensure_digest, updated generate-agent-digest references, and removed unused constants.

- [2026-11-10] **[Verify]**
  Verified 141 passed in test_agent_files.py and test_agent_digest.py (task-217), clean ruff checks, and --repo-root CLI reproduction.
  - Files touched: 6.
  - Lines touched: 170.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude: Approved.
  - Findings: [review-findings-2.md](T0019-port-the-dev-guidelines-agent-digest-generator-into/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

