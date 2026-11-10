---
id: T0052
owner: "@claude"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T07:52:43Z"
ended_at: "2026-11-10T07:55:49Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-reviewer"
completion-commit: a3bf8f28e9003979913185bf2be856508c5eccc6
---
# T0052: Move the README Git, file, locking, process, Markdown, duration, and rate limiter sections into docs/tutorials pages

## Goals
Move these README sections into short `docs/tutorials/` pages without losing content:
"Git repository helpers", "Locking", "Process hierarchy and safe termination", "Atomic text file helpers",
"Markdown table helpers", the library part of "Markdown linter", "Duration and time formatting helpers", and "Task rate limiter".
Replace each moved README section with a one-line summary linking its tutorial.
Repoint `docs/index.md` links that target removed README anchors.
Bump the `-pre` patch version and record the move in `CHANGELOG.md`.

## Task Execution Steps
- [x] **[Read]**      Read the README sections, docs/index.md, docs/tools/processes.md, and docs/tools/lint-markdown.md.
- [x] **[Doc]**       Write the five tutorials from the README sections, fixing typos and trailing whitespace.
- [x] **[Doc]**       Replace the moved README sections with linked summaries, and repoint docs/index.md links.
- [x] **[Doc]**       Bump pyproject.toml and the CHANGELOG.md heading, and add a Docs entry.
- [x] **[Verify]**    Run the completion check and confirm no README anchor link targets a removed section.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  Split from the 2026-11-10 README restructuring request; follows T0050.

- [2026-11-10] **[Doc]**
  Moved the eight README sections into five tutorials, added a verified linter library example, and added a started-after example to docs/tools/processes.md.

- [2026-11-10] **[Decide]**
  Skipped the manual version bump: plan tasks stop bumps the -pre patch version itself, as the T0050 commit showed.
  - Touched undeclared docs/tools/processes.md, as the spec anticipated; recount is 9 files.

- [2026-11-10] **[Verify]**
  The completion check exited 0, and all eight tutorial snippets ran cleanly.
  - Files touched: 9.
  - Lines touched: 467.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-reviewer: All eight README sections moved intact; the new linter example runs as documented, and links, lint, and validation pass; three optional nits.
  - Findings: [review-findings-1.md](T0052-move-the-readme-git-file-locking-process-markdown/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Applied review nit N3, linking tools/processes.py from the process management tutorial; N1 and N2 need no change.

- [2026-11-10] **[Complete]**
  Task completed successfully.

