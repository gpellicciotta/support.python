---
id: T0049
owner: "@claude"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T07:25:58Z"
ended_at: "2026-11-10T07:32:36Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 2
reviewed_by: "@claude-reviewer"
completion-commit: 70afcd5059706d53516c56d76eed8aa5e3fa2fe2
---
# T0049: Move the README DevOps helpers section into a docs/tutorials/devops-scripts.md tutorial and link it from the README

## Goals
Create `docs/tutorials/devops-scripts.md`, a short tutorial on the `support_python.devops` package and its main uses.
Move the README "DevOps script helpers and environment managers" section into it without losing content.
Replace the README section with a one-paragraph summary linking the tutorial.
Repoint the `docs/index.md` and `docs/migration-v2.md` links that target the removed README anchor.
Bump the `-pre` patch version and record the move in `CHANGELOG.md`.

## Task Execution Steps
- [x] **[Decided]**   Use docs/tutorials for package tutorials and keep docs/tools as the CLI references.
- [x] **[Read]**      Read the README DevOps section, docs/index.md, and docs/migration-v2.md links to it.
- [x] **[Doc]**       Write docs/tutorials/devops-scripts.md from the README section, fixing trailing whitespace and table layout.
- [x] **[Doc]**       Replace the README section with a linked summary, and repoint index and migration links.
- [x] **[Doc]**       Bump pyproject.toml and the CHANGELOG.md heading, and add a Docs entry.
- [x] **[Verify]**    Run the completion check and confirm no README anchor link targets the removed section.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  User asked on 2026-11-10 to move README package docs into short docs/tutorials pages. Split into T0049, T0050, T0052, and T0051 to stay below the large line.

- [2026-11-10] **[Doc]**
  Moved the README DevOps section into docs/tutorials/devops-scripts.md, fixing its table layout and trailing whitespace.

- [2026-11-10] **[Decide]**
  Kept the user's uncommitted README edits as the base. Left concurrent src/support_python cli.py and agent_files.py edits from another actor out of this task.

- [2026-11-10] **[Verify]**
  The completion check exited 0, and no link targets the removed README anchor.
  - Files touched: 6.
  - Lines touched: 520.
  - Reopenings: 0.
  - Size note: above the typical line, as estimated.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude-reviewer: The tutorial drops two README statements (the help/version actions and the post-freeze release-asset sentence); the other checks pass.
  - Findings: [review-findings-1.md](T0049-move-the-readme-devops-helpers-section-into-a/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Reworked review round 1: restored the help/version and post-freeze asset sentences, scoped the export claim, and split the proxy bullet.
  - The user's uncommitted README edit had dropped both restored sentences.

- [2026-11-10] **[Verify]**
  The completion check exits 0 after rework.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude-reviewer: All round 1 findings are fixed; the tutorial keeps every README DevOps statement and all checks pass.
  - Findings: [review-findings-2.md](T0049-move-the-readme-devops-helpers-section-into-a/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

