---
id: T0050
owner: "@claude"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T07:50:04Z"
ended_at: "2026-11-10T07:52:42Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 1
reviewed_by: "@claude-reviewer"
completion-commit: 988984671d017fbc989771ecd241dfbcd59059da
---
# T0050: Move the README CLI, logging, script utility, REST client, view capture, and SQL sections into docs/tutorials pages

## Goals
Move these README sections into short `docs/tutorials/` pages without losing content:
"Shared CLI helpers, tabular output, and session storage", "CLI logging", "Common script utilities",
"REST client HTTP transport", "REST client error hierarchy and status mapping", "View Capture Engine and Static Server",
"SQL Snapshot Anonymizer", and "Models and wire helpers".
Replace each moved README section with a one-line summary linking its tutorial.
Repoint `docs/index.md` links that target removed README anchors.
Bump the `-pre` patch version and record the move in `CHANGELOG.md`.

## Task Execution Steps
- [x] **[Read]**      Read the eight README sections, docs/index.md, and the devops-scripts tutorial for style.
- [x] **[Doc]**       Write the five tutorials from the README sections, fixing typos and trailing whitespace.
- [x] **[Doc]**       Replace the moved README sections with linked summaries, and repoint docs/index.md links.
- [x] **[Doc]**       Bump pyproject.toml and the CHANGELOG.md heading, and add a Docs entry.
- [x] **[Verify]**    Run the completion check and confirm no README anchor link targets a removed section.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  Split from the 2026-11-10 README restructuring request; follows T0049, which sets the tutorial style.

- [2026-11-10] **[Doc]**
  Moved eight README sections into five tutorials, added import sys to the logging example, and listed the tutorials in docs/index.md.

- [2026-11-10] **[Verify]**
  The completion check exited 0, and five tutorial snippets ran cleanly.
  - The token snippet wrote ~/.support-python, which I removed afterwards.
  - Files touched: 9.
  - Lines touched: 462.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-reviewer: All eight README sections moved intact into five tutorials; claims, links, anchors, lint, version, and task validation check out.
  - Findings: [review-findings-1.md](T0050-move-the-remaining-readme-library-sections-into-short/review-findings-1.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

