---
id: T0017
owner: "@gemini"
session: antigravity-20261107-9e8b68
needs: []
branch: task/T0017-parameterize-the-ported-agent-files-sync-with-configurable
worktree: .plan/work/T0017-parameterize-the-ported-agent-files-sync-with-configurable
status: completed
started_at: "2026-11-07T17:39:47Z"
ended_at: "2026-11-07T18:21:27Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 4092.2, input: 933374, output: 233076, cache_read: 24774924}
  review: {turns: 4, duration_s: 751.8, input: 112, output: 28410, cache_read: 2910280, cache_write: 199850}
review_status: approved
review_round: 2
work_duration: 2498.5
reviewed_by: "@claude"
completion-commit: 98420d2bf9f986d33f26705f61fa98df62cd9764
---
# T0017: Parameterize the ported agent-files sync with configurable digest, skills, marker, and tool registry

## Goals
Replace the hard-coded repository root, digest path, skills directory, marker text, manifest source name, and `LEGACY_SKILL_NAMES` with settings from `agent-files.json` and flags.
Make the tool registry data-driven, with `claude`, `antigravity`, and `codex` as default entries.
Keep the current marker text working so installed files do not change.
Prerequisite: T0015 merged. Ends with release 1.3.0 prepared per `docs/devops.md`.

Completion check: dev-guidelines config yields an empty dry-run diff, and a second fixture project with another marker syncs correctly.
Size estimate: 5 files, 300 lines.

## Task Execution Steps
- [x] **[Read]**      List every hard-coded dev-guidelines value in agent_files.py and how each is used.
- [x] **[Implement]** Author failing tests for config loading, a second marker, and an added tool entry.
- [x] **[Verify]**    Run the new tests and confirm they fail for the expected reasons.
- [x] **[Implement]** Add the JSON config loader, flags, and the data-driven tool registry.
- [x] **[Verify]**    Run the full suite and confirm the dev-guidelines config gives an empty dry-run diff.
- [x] **[Doc]**       Document the config schema, update CHANGELOG.md, and prepare the 1.3.0 release.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.

- [2026-11-07] **[Read]**
  Cataloged hard-coded dev-guidelines values and tool registry sites in agent_files.py.
  - REPO_ROOT, DIGEST_PATH, and SKILLS_DIR path resolvers.
  - MARKER_BEGIN, MARKER_END, SKILLS_MANIFEST_NAME, SKILLS_MANIFEST_SOURCE, and LEGACY_SKILL_NAMES.
  - TOOLS list across list, select, validation, and harness.

- [2026-11-07] **[Verify]**
  Authored config, second-marker, and tool-registry tests and confirmed red-phase failures.
  - 6 new tests failed on missing agent_files_config and --config flag.

- [2026-11-07] **[Implement]**
  Implemented agent_files_config.py and parameterized agent_files.py with JSON config, CLI flags, and ToolRegistry.
  - Added AgentFilesConfig, ToolRegistry, and strict JSON schema validation.
  - Wired --config, path, marker, manifest, and legacy-skill CLI flags.

- [2026-11-07] **[Doc]**
  Documented agent-files.json schema in docs/agent-files.md, updated CHANGELOG.md, and prepared release 1.3.0.
  - Touched undeclared pyproject.toml to set version 1.3.1-pre after freezing 1.3.0.
  - Size note: 6 files and 731 lines keep config, CLI, tests, and docs atomic.

- [2026-11-07] **[Verify]**
  Verified full pytest suite (task-138), ruff checks, package build (task-144), and dev-guidelines dry-run diff identical to baseline.
  - Files touched: 6.
  - Lines touched: 731.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 rejected by @claude: The code meets the functional goals; the rejection is for documentation drift only.
  - Findings: [review-findings-1.md](T0017-parameterize-the-ported-agent-files-sync-with-configurable/review-findings-1.md).

- [2026-11-07] **[Doc]**
  Updated README.md, docs/agent-files.md, docs/index.md, CLAUDE.md, and the --digest help label for review round 1.
  - Touched undeclared README.md, docs/index.md, and CLAUDE.md to resolve documentation drift.
  - Size note: 9 files and 759 lines keep config, CLI, tests, and docs atomic.

- [2026-11-07] **[Verify]**
  Verified agent-files tests, ruff, package build (task-52), and dev-guidelines dry-run diff identical to baseline.
  - Files touched: 9.
  - Lines touched: 759.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 2 approved by @claude: All five round-1 rework items are resolved; the work meets the T0017 goals.
  - Findings: [review-findings-2.md](T0017-parameterize-the-ported-agent-files-sync-with-configurable/review-findings-2.md).

- [2026-11-07] **[Complete]**
  Task completed successfully.

