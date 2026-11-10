---
id: T0020
owner: "@gemini"
session: antigravity-20261110-92e0d7
needs: []
branch: task/T0020-generalize-agent-digest-to-take-markdown-paths-order
worktree: .plan/work/T0020-generalize-agent-digest-to-take-markdown-paths-order
status: completed
started_at: "2026-11-10T00:04:03Z"
ended_at: "2026-11-10T00:41:40Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 6, duration_s: 3532.4, input: 923598, output: 203052, cache_read: 16627998}
  review: {turns: 4, duration_s: 831.0, input: 116, output: 36164, cache_read: 3219624, cache_write: 235444}
work_duration: 2256.8
review_status: approved
review_round: 2
reviewed_by: "@claude"
completion-commit: 19230d3685f45aea01175a80bcadea750e54764b
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
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided: validate takes paths and also checks freshness; outputs default to ./agent-digest.md and ./agent-skills.

- [2026-11-09] **[Decide]**
  User changed the decision on 2026-11-09: `check` replaces `validate`, matching the ADR-0003 verb convention.

- [2026-11-10] **[Read]**
  Read agent_digest.py, agent_files.py, test_agent_digest.py, test_agent_files.py, cli.py, logging.py, git.py, and dev-guidelines layout constants.

- [2026-11-10] **[Verify]**
  Verified red-phase failures for path collection, index ordering, output options, link-base derivation, and merged check.

- [2026-11-10] **[Implement]**
  Generalized agent-digest to accept <PATH>... inputs, order by front-matter index, rewrite /skills/<name>/SKILL.md links, derive --link-base from Git origin, fold validate into check with --skill-index, and update agent-files and docs.
  - Files touched: 8.
  - Lines touched: 2059.
  - Reopenings: 0.

- [2026-11-10] **[Doc]**
  Authored docs/tools/agent-digest.md and updated README.md, docs/index.md, CHANGELOG.md, and validation-proof.md.

- [2026-11-10] **[Verify]**
  Verified 136 passed tests across test_agent_digest.py, test_agent_files.py, and test_console_scripts.py, ruff check/format clean, lint-markdown clean across docs, and zero-diff agent-digest check on dev-guidelines.

- [2026-11-10] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-10] **[Doc]**
  Added missing step-coverage log entries for Read and Doc to resolve TF020 before review.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Size]**
  Size note: diff is 8 files and 2063 lines, above the large line but under three times the 700-line estimate.
  - Accepted by the orchestrator under the user's size delegation.
  - Most lines rework the ported generator; splitting would leave it half-generalized.

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude: The code change meets the technical spec, but the new tool documentation describes behavior that does not exist.
  - Findings: [review-findings-1.md](T0020-generalize-agent-digest-to-take-markdown-paths-order/review-findings-1.md).

- [2026-11-10] **[Doc]**
  Rewrote docs/tools/agent-digest.md to match implemented options, front-matter keys, link rewriting, and check rules, and updated validation-proof.md with base-commit red-phase output and dev-guidelines generate proof.

- [2026-11-10] **[Implement]**
  Formatted startup banner paths with as_posix() and cached missing link_base fallback in build_skills and build_digest.

- [2026-11-10] **[Verify]**
  Verified test_agent_digest.py (26 passed, 15 subtests), ruff check/format, lint-markdown on docs/tools/agent-digest.md, and zero-diff generate on dev-guidelines.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude: Round 2 resolves every round-1 defect and process gap; the work meets the task goals.
  - Findings: [review-findings-2.md](T0020-generalize-agent-digest-to-take-markdown-paths-order/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

