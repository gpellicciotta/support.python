---
id: T0024
owner: "@gemini"
session: antigravity-20261109-4e3d15
needs: []
branch: task/T0024-replace-the-support-python-command-with-lint-markdown
worktree: .plan/work/T0024-replace-the-support-python-command-with-lint-markdown
status: completed
started_at: "2026-11-09T19:56:03Z"
ended_at: "2026-11-09T20:13:44Z"
review: agent
preview: none
protocol: standard
size_status: approved
size_estimate: 25 files, 2826 lines
usage:
  worker: {turns: 6, duration_s: 3591.0, input: 1317030, output: 127478, cache_read: 27142550}
  review: {turns: 4, duration_s: 720.0, input: 88, output: 24842, cache_read: 2389072, cache_write: 129108}
work_duration: 3290.6
size_approved: 25 files, 2826 lines
size_approved_by: "@Giovanni Pellicciotta (delegated)"
size_approved_at: "2026-11-09T19:39:18Z"
review_status: approved
review_round: 2
reviewed_by: "@claude"
completion-commit: 86225345037c66b2f05c339763fdfae997184a73
---
# T0024: Replace the support-python command with lint-markdown, agent-files, and git-repository-backup console scripts, and drop the wrapper scripts

## Goals
Remove the `support-python` console script, `src/support_python/__main__.py`, and the demo `greet` CLI from `support_python.cli`.
Register `lint-markdown`, `agent-files`, and `git-repository-backup` console scripts beside `processes`, at the current module paths.
Rename agent-files' `TOOL_NAME` from `update-global-agent-files` to `agent-files`.
Delete the checkout wrappers and duplicated helpers under `scripts/` listed in the technical spec, with their tests.
Document per-user and global installation of the tools in `README.md`.

## Task Execution Steps
- [x] **[Read]**      Read cli.py main, the pyproject scripts table, the wrapper scripts, and every test using them.
- [x] **[Implement]** Write tests/test_console_scripts.py covering entry points, banners, and the removed support-python command.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Update pyproject.toml, cli.py, package exports, and the agent-files TOOL_NAME; delete the listed files.
- [x] **[Verify]**    Reinstall editable, run the full suite, and run each console script's version action.
- [x] **[Doc]**       Update README.md, CHANGELOG.md, docs/requirements.md, docs/agent-files.md, and docs/markdown-lint.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  Scope agreed with the user on 2026-11-09 as part of the v2.0.0 standalone-tools and reusable-devops restructuring. The user confirmed tools run directly from the terminal, so the wrappers go.

- [2026-11-09] **[Implement]**
  Replaced support-python and wrapper scripts with processes, agent-files, lint-markdown, and git-repository-backup console scripts.
  - Undeclared test files updated: 4.
  - Counted files excluding deletions: 15 (433 lines).

- [2026-11-09] **[Verify]**
  Verified editable install, console script version banners, lint-markdown check, and full pytest suite.
  - 693 passed, 3 skipped.
  - All 4 console scripts verified.

- [2026-11-09] **[Verify]**
  Recorded task outcomes.
  - Files touched: 15.
  - Lines touched: 433.
  - Reopenings: 0.

- [2026-11-09] **[Size]**
  Size approval requested by the work loop: 25 files, 2826 lines exceeds 8x the approved 11 files, 350 lines.

- [2026-11-09] **[Size]**
  Size approved by @Giovanni Pellicciotta (delegated) for 25 files, 2826 lines.
  - Decided by the Claude Code orchestrator under the user's size delegation.
  - Counted diff is 15 files, 432 lines, excluding deleted files.
  - The loop total included 10 wholly deleted files, 2394 lines.

- [2026-11-09] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-09] **[Review]**
  Round 1 rejected by @claude: Reviewed branch tip `2957fd7` (base `886c224`), not `decca33`.
  - Findings: [review-findings-1.md](T0024-replace-the-support-python-command-with-lint-markdown/review-findings-1.md).

- [2026-11-09] **[Verify]**
  Recorded red-phase failure proof for tests/test_console_scripts.py before implementation (10 failed; details in validation-proof.md).

- [2026-11-09] **[Implement]**
  Addressed review round 1 findings and rebased onto main (decca33, v2.0.2-pre).
  - Updated CLI references in docs/index.md, CLAUDE.md, CHANGELOG.md, agent_files.py, and test_agent_files.py.
  - Used sysconfig scripts path and un-resolved sys.executable parent in console script tests.
  - Counted files excluding deletions: 17 (460 lines).

- [2026-11-09] **[Verify]**
  Verified editable install, console scripts, ruff, lint-markdown, and pytest on rebased commit 180ab88.
  - 694 passed, 3 skipped in 187.46s.
  - All 4 console scripts emit v2.0.2-pre+180ab88 banners.

- [2026-11-09] **[Verify]**
  Recorded updated task outcomes.
  - Files touched: 17.
  - Lines touched: 460.
  - Reopenings: 0.

- [2026-11-09] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-09] **[Review]**
  Round 2 approved by @claude: Approved.
  - Findings: [review-findings-2.md](T0024-replace-the-support-python-command-with-lint-markdown/review-findings-2.md).

- [2026-11-09] **[Complete]**
  Task completed successfully.

