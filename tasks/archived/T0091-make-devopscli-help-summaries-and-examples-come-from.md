---
id: T0091
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T15:01:26Z"
ended_at: "2026-11-10T15:11:36Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-code-reviewer"
completion-commit: 24e2e73df0f9704cd5e49719979d12a6b999ca71
---
# T0091: Make DevopsCli help summaries and examples come from the project adapter, so GradleProject help describes Gradle tasks

## Goals
template.java T0030 found that `DevopsCli` help describes Python behavior for every adapter.
It shows a pytest `test` example and says `check` runs lint, test, and build, while `GradleProject` runs one `build`.
Add `Project.action_summaries()` and `Project.test_selection_example`, and let `DevopsCli` use them.
Make `GradleProject` name its Gradle tasks and `release_task` in its help.
Warn when `release --skip-checks` meets a project with its own release, where it does nothing.
Completion check: `python scripts/devops.py check`.
Size estimate: 7 files, 130 lines

## Task Execution Steps
- [x] **[Implement]** Add help summary, example, and `--skip-checks` tests for Gradle, Python, and Node adapters.
- [x] **[Verify]**    Run the new tests and record their failure output.
- [x] **[Implement]** Add `action_summaries` and `test_selection_example`, and use them in `DevopsCli`.
- [x] **[Verify]**    Run `python scripts/devops.py check` and record the output.
- [x] **[Doc]**       Update the DevOps scripts tutorial and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Verify]**
  Recorded six failing help tests, then a green check with 1192 tests passing.

- [2026-11-10] **[Implement]**
  Added Project.action_summaries and test_selection_example; DevopsCli uses them, GradleProject names its tasks, and --skip-checks warns on own releases.

- [2026-11-10] **[Doc]**
  Documented adapter help in the DevOps scripts tutorial and CHANGELOG.md.

- [2026-11-10] **[Review]**
  Agent review approved; fixed empty-list wording, the check summary, a weak assertion, and documented that DevopsCli reads help once.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-reviewer.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 7.
  - Lines touched: 118.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

