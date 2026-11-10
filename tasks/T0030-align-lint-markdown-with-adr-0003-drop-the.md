---
id: T0030
owner: "@gemini"
session: antigravity-20261110-ae1428
needs: []
branch: task/T0030-align-lint-markdown-with-adr-0003-drop-the
worktree: .plan/work/T0030-align-lint-markdown-with-adr-0003-drop-the
status: active
started_at: "2026-11-10T00:42:00Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 1355.8, input: 503910, output: 65250, cache_read: 12716666}
review_status: pending
review_round: 1
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
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

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

