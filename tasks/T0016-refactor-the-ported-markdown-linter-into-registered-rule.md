---
id: T0016
owner: "@gemini"
session: antigravity-20261107-2e866f
needs: []
branch: task/T0016-refactor-the-ported-markdown-linter-into-registered-rule
worktree: .plan/work/T0016-refactor-the-ported-markdown-linter-into-registered-rule
status: completed
started_at: "2026-11-07T18:21:46Z"
ended_at: "2026-11-07T19:10:49Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 4, duration_s: 5021.0, input: 974704, output: 223288, cache_read: 25422580}
  review: {turns: 4, duration_s: 724.4, input: 100, output: 18940, cache_read: 2260772, cache_write: 160666}
review_status: approved
review_round: 2
work_duration: 2943.4
reviewed_by: "@claude"
completion-commit: fd9b89fe23fcd22fc94a0d12387cf59aca0e05fc
---
# T0016: Refactor the ported Markdown linter into registered rule classes with loadable profiles

## Goals
Split the `MarkdownLinter` if-ladder into small rule classes in a `support_python.markdown` package with a rule registry.
Keep every `MD0xx` ID and message stable.
Add profiles loaded from `.markdown-lint.json`: a default profile with the generic rules and a `dev-guidelines` profile enabling `MD015` and the historical-task logic.
Prerequisite: T0014 merged.

Completion check: the ported tests pass unchanged, and profile tests pass.
Size estimate: 10 files, 900 lines.
Size note: Above the typical line because rule classes replace one 1,600-line module; no behavior changes beyond profile loading, so output stays comparable with T0014.

## Task Execution Steps
- [x] **[Read]**      List every MD rule, its trigger conditions, and its dependencies on shared linter state.
- [x] **[Implement]** Author failing tests for the registry, profile loading, and the dev-guidelines profile.
- [x] **[Verify]**    Run the new tests and confirm they fail for the expected reasons.
- [x] **[Implement]** Create the markdown package, registry, and rule classes while keeping existing tests green.
- [x] **[Implement]** Add JSON profile loading and the default and dev-guidelines profiles.
- [x] **[Verify]**    Run the full suite and diff linter output against T0014 on dev-guidelines.
- [x] **[Doc]**       Document profiles in docs and update CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.

- [2026-11-07] **[Read]**
  Cataloged MD001-MD019 trigger conditions, shared document context state, and profile-specific MD015 and historical-task exemptions.

- [2026-11-07] **[Verify]**
  Authored test_markdown_profiles.py and confirmed red-phase ImportError on missing markdown package rule registry and profiles.

- [2026-11-07] **[Implement]**
  Implemented support_python.markdown package with RuleRegistry, MD001-MD019 rule classes, and loadable default and dev-guidelines JSON profiles.

- [2026-11-07] **[Verify]**
  Step 6: Passed ruff check, ruff format --check, and full pytest suite (752 passed, 3 skipped); verified 100% parity with dev-guidelines/scripts/lint-markdown.py across 54 main files (0 issues) and 258 task files (136 identical issues).

- [2026-11-07] **[Doc]**
  Documented Markdown lint profiles in docs/markdown-lint.md, updated CHANGELOG.md, and recorded validation-proof.md.

- [2026-11-07] **[Size]**
  Size note: Rule classes replace one 1,600-line module while keeping T0014 output comparable.
  - Files touched: 9.
  - Lines touched: 1309 insertions, 502 deletions (net +807).
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 rejected by @claude: The rule split, registry, and JSON profile loading work.
  - Findings: [review-findings-1.md](T0016-refactor-the-ported-markdown-linter-into-registered-rule/review-findings-1.md).

- [2026-11-07] **[Implement]**
  Addressed Round 1 review findings: moved markdown.py to markdown/tables.py, unified default CLI profile resolution, and updated README.md, CLAUDE.md, docs/index.md, and docs/markdown-lint.md.

- [2026-11-07] **[Verify]**
  Re-verified ruff check, ruff format --check, full pytest suite (752 passed, 3 skipped), and dev-guidelines parity.
  - Files touched: 13.
  - Lines touched: 1338 insertions, 508 deletions (net +830).
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 2 approved by @claude: Both Round 1 defects are fixed.
  - Findings: [review-findings-2.md](T0016-refactor-the-ported-markdown-linter-into-registered-rule/review-findings-2.md).

- [2026-11-07] **[Complete]**
  Task completed successfully.

