---
id: T0014
owner: "@gemini"
session: antigravity-20261107-e1de8e
needs: []
branch: task/T0014-port-the-markdown-linter-into-support-python-with
worktree: .plan/work/T0014-port-the-markdown-linter-into-support-python-with
status: active
started_at: "2026-11-07T16:33:49Z"
ended_at: —
review: agent
preview: none
protocol: standard
usage:
  worker: {turns: 2, duration_s: 2044.8, input: 976078, output: 48250, cache_read: 23124486}
  review: {turns: 2, duration_s: 320.8, input: 44, output: 9328, cache_read: 872072, cache_write: 62128}
review_status: rejected
review_round: 1
reviewed_by: "@claude"
work_duration: 1214.9
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
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

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

