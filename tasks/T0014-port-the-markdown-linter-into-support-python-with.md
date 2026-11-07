---
id: T0014
owner: "@gemini"
session: antigravity-20261107-e1de8e
needs: []
branch: task/T0014-port-the-markdown-linter-into-support-python-with
worktree: .plan/work/T0014-port-the-markdown-linter-into-support-python-with
status: completed
started_at: "2026-11-07T16:33:49Z"
ended_at: "2026-11-07T17:14:30Z"
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 6, duration_s: 3908.2, input: 1719868, output: 94296, cache_read: 47411782}
  review: {turns: 6, duration_s: 786.4, input: 112, output: 24814, cache_read: 2263206, cache_write: 198584}
review_status: approved
review_round: 3
work_duration: 2441.6
reviewed_by: "@claude"
completion-commit: d9f4c53635d2be2df62c44d9271a1c60d924c5df
---
# T0014: Port the Markdown linter into support_python unchanged with a lint markdown CLI and ported tests

## Goals
Copy dev-guidelines `scripts/lint-markdown.py` into `support_python.markdown_lint` unchanged apart from imports.
Expose it as `support-python lint markdown [paths] [--fix] [--offline]` with identical rules and output.
Rule classes and profiles follow in T0016.
Prerequisite: T0013 merged.

Completion check: the ported tests pass and `support-python lint markdown` reports the same issues as the original script on dev-guidelines.
Size estimate: 4 files, 60 hand-written lines plus mechanical copies.
Mechanical command: `Copy-Item {{dev-guidelines}}/scripts/lint-markdown.py src/support_python/markdown_lint.py`
Mechanical command: `Copy-Item {{dev-guidelines}}/scripts/tests/test_lint_markdown.py tests/test_markdown_lint.py`

## Task Execution Steps
- [x] **[Read]**      Read lint-markdown.py imports and its harness usage to plan the import fixes.
- [x] **[Implement]** Copy the linter and its tests, then fix imports so the tests collect and fail.
- [x] **[Verify]**    Confirm the ported tests fail only on the missing CLI registration.
- [x] **[Implement]** Register the lint markdown subcommand in support_python.cli.
- [x] **[Verify]**    Run the full suite and compare output against the original script on dev-guidelines.
- [x] **[Doc]**       Update CHANGELOG.md and docs with the lint markdown command.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-06] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-06] **[Decide]**
  Scope drafted from the approved dev-guidelines migration plan; configs use JSON.

- [2026-11-07] **[Read]**
  Read lint-markdown.py and test_lint_markdown.py imports, REPO_ROOT usage, and ToolHarness integration.

- [2026-11-07] **[Verify]**
  Copied markdown_lint.py and test_markdown_lint.py, fixed imports, and confirmed tests fail only on missing CLI registration (114 passed, 1 failed).

- [2026-11-07] **[Implement]**
  Registered lint markdown subcommand in support_python.cli and moved stream reconfiguration into markdown_lint.main().

- [2026-11-07] **[Verify]**
  Verified full pytest suite (653 passed, 3 skipped), ruff checks, and identical output against dev-guidelines.
  - Files touched: 4.
  - Lines touched: 64.
  - Reopenings: 0.

- [2026-11-07] **[Doc]**
  Updated CHANGELOG.md, pyproject.toml, and docs/index.md with support-python lint markdown.
  - Touched undeclared docs/index.md and pyproject.toml required by Step 6.

- [2026-11-07] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 1 rejected by @claude: The port is close to the original and mostly meets the goals, but it has one behavioral regression that the.
  - Findings: [review-findings-1.md](T0014-port-the-markdown-linter-into-support-python-with/review-findings-1.md).

- [2026-11-07] **[Decided]**
  Resolved REPO_ROOT via find_project_root(Path.cwd()), root-relative MD014 links against current_project_root, and sibling GitHub URLs against the workspace root.
  - Bumped active version to v1.0.19-pre in CHANGELOG.md and pyproject.toml.

- [2026-11-07] **[Implement]**
  Restored original dev-guidelines test fixtures, added root-relative MD014 test, and documented support-python lint markdown in README.md.
  - Touched undeclared README.md required by Round 1 review.

- [2026-11-07] **[Verify]**
  Verified 654 passed tests, clean ruff checks, and matching dev-guidelines lint output (differing only in version banner and elapsed time).
  - Files touched: 5.
  - Lines touched: 100.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 2 rejected by @claude: Round 1 rework is mostly resolved, but one restored test passes only on this machine.
  - Findings: [review-findings-2.md](T0014-port-the-markdown-linter-into-support-python-with/review-findings-2.md).

- [2026-11-07] **[Decided]**
  Added _resolve_workspace_root (.plan/work-aware) and repo_name == base_root.name matching so MD018 resolves current and sibling repositories.

- [2026-11-07] **[Implement]**
  Isolated dev-guidelines fixture tests in temporary workspaces, switched README end-to-end check to LICENSE.md, and added CLI/MD014 tests.

- [2026-11-07] **[Verify]**
  Verified all 654 tests pass and ruff check/format are clean on the self-contained test suite.
  - Files touched: 5.
  - Lines touched: 121.
  - Reopenings: 0.

- [2026-11-07] **[Review]**
  Round 3 requested (mode: agent).

- [2026-11-07] **[Review]**
  Round 3 approved by @claude: The Round 2 defect is fixed.
  - Findings: [review-findings-3.md](T0014-port-the-markdown-linter-into-support-python-with/review-findings-3.md).

- [2026-11-07] **[Complete]**
  Task completed successfully.

