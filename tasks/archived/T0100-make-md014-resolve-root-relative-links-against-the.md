---
id: T0100
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T17:04:17Z"
ended_at: "2026-11-10T17:09:44Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@codex"
completion-commit: 3fc8c5a6598ae740a7cb726e8fd1fba36aa6d181
---
# T0100: Make MD014 resolve root-relative links against the project root on POSIX, where they now count as absolute and are skipped

## Goals
Make `MD014` resolve root-relative links such as `/docs/guide.md` against the project root on POSIX too.
POSIX counts them as absolute paths, so the rule skipped them and CI on Linux failed.
Keep skipping protocol-relative `//host` links and drive-letter or UNC absolute paths.
Completion check: `python scripts/devops.py check`, then the GitHub Linux CI job
Size estimate: 3 files, 40 lines

### Declared Files
- src/support_python/markdown/rules.py
- tests/test_markdown_lint.py
- CHANGELOG.md

### Tests
- Unit: with a POSIX-like `Path.is_absolute`, `/docs/missing.md` is reported and `/docs/guide.md` is not.
- Integration: the existing root-relative test passes in the Linux CI job.

## Task Execution Steps
- [x] **[Implement]** Author a root-relative link test that simulates POSIX absolute paths.
- [x] **[Verify]**    Run it and record the failure, plus the Linux CI failure.
- [x] **[Implement]** Resolve single-leading-slash links against the project root before the absolute check.
- [x] **[Verify]**    Run `python scripts/devops.py check` and record the output.
- [x] **[Doc]**       Add the CHANGELOG.md entry.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @codex: No correctness bugs on Windows or POSIX; exclusion tests would be nice-to-have.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 3.
  - Lines touched: 32.
  - Reopenings: 0.

- [2026-11-10] **[Implement]**
  Resolved single-leading-slash links against the project root before the absolute-path check in MD014.

- [2026-11-10] **[Complete]**
  Task completed successfully.

