---
id: T0030
owner: "@gemini"
session: antigravity-20261110-ae1428
needs: []
branch: task/T0030-align-lint-markdown-with-adr-0003-drop-the
worktree: .plan/work/T0030-align-lint-markdown-with-adr-0003-drop-the
status: completed
started_at: "2026-11-10T00:42:00Z"
ended_at: "2026-11-10T01:16:53Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 2286.6, input: 1108874, output: 92512, cache_read: 27552642}
  review: {turns: 8, duration_s: 1781.6, input: 120, output: 32852, cache_read: 3039984, cache_write: 204680}
review_status: approved
review_round: 2
work_duration: 2093.1
reviewed_by: "@claude"
completion-commit: c348d767a45c54a99996574e4a266b71a40e2999
---
# T0030: Align lint-markdown with ADR-0003: drop the --fix flag, add JSON check output, and rename its config to .lint-markdown.json

## Goals
Remove lint-markdown's `--fix` global flag, so the `fix` action is the only writing path, and give `fix` a `--dry-run` option.
Add `--format text|json` to `check`.
Rename the default config to `.lint-markdown.json`, reading `.markdown-lint.json` with a warning.
Keep exit codes 0 for clean, 1 for violations or failure, and 2 for invalid arguments.

## Task Execution Steps
- [x] **[Read]**      Read the lint-markdown actions, the --fix flag handling, issue reporting, and profile config lookup.
- [x] **[Implement]** Write failing tests for the removed flag, fix --dry-run, JSON output, and both config names.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Remove --fix, add fix --dry-run and check --format, and add the config fallback.
- [x] **[Verify]**    Run the full suite and the installed integration commands from the technical spec.
- [x] **[Doc]**       Update docs/tools/lint-markdown.md, README.md, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided on 2026-11-09 to rename .markdown-lint.json to .lint-markdown.json; legacy reading with a warning follows ADR-0003.

- [2026-11-10] **[Verify]**
  Verified red-phase failures for removed --fix flag, fix --dry-run, check --format json, and config fallback.
  - 9 failed, 36 passed in targeted pytest run.

- [2026-11-10] **[Implement]**
  Removed --fix flag, added fix --dry-run and check --format text|json, and renamed default config to .lint-markdown.json with legacy fallback warning.

- [2026-11-10] **[Verify]**
  Verified full pytest suite and CLI integration commands.
  - 744 passed, 3 skipped.
  - JSON output and legacy config warning verified.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 8.
  - Lines touched: 355.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude: Most goals are met, and the change is tidy and well tested.
  - Findings: [review-findings-1.md](T0030-align-lint-markdown-with-adr-0003-drop-the/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Addressed review round 1 findings: preserved stderr in JSON mode, removed manual json_mode toggles, and resolved config per directory.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 8.
  - Lines touched: 366.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude: Approved.
  - Findings: [review-findings-2.md](T0030-align-lint-markdown-with-adr-0003-drop-the/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

