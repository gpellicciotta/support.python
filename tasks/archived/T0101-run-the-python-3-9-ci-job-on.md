---
id: T0101
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T17:08:30Z"
ended_at: "2026-11-10T17:18:43Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@codex"
completion-commit: 9a87805a8fb99e62654975a01cf0dd4ebf372baf
---
# T0101: Run the Python 3.9 CI job on ubuntu-24.04, since setup-python has no 3.9 for the ubuntu-latest image

## Goals
Run the Python 3.9 CI job on `ubuntu-24.04`, since `setup-python` has no 3.9 for the `ubuntu-latest` image.
Keep the latest 3.x job on `ubuntu-latest`, and document the runner choice in `docs/devops.md`.
Completion check: both GitHub CI jobs on `main` succeed
Size estimate: 3 files, 20 lines

### Declared Files
- .github/workflows/python-package.yml
- docs/devops.md
- CHANGELOG.md

### Tests
- Unit test: none (workflow configuration; GitHub Actions runs it)
- Integration: the 3.9 job installs Python and runs the suite on `ubuntu-24.04`.

## Task Execution Steps
- [x] **[Verify]**    Record the 3.9 setup failure on `ubuntu-latest` from CI.
- [x] **[Implement]** Pin the 3.9 matrix entry to `ubuntu-24.04` through a matrix include.
- [x] **[Verify]**    Push and confirm both CI jobs succeed.
- [x] **[Doc]**       Document the runner choice in docs/devops.md and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @codex: No correctness bugs; CI run 42863145089 passed both jobs.

- [2026-11-10] **[Implement]**
  Pinned the 3.9 matrix entry to ubuntu-24.04 through a matrix include.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 3.
  - Lines touched: 11.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

