---
id: T0051
owner: "@claude"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T07:55:57Z"
ended_at: "2026-11-10T07:59:46Z"
review: agent
preview: none
protocol: standard
review_status: approved
review_round: 2
reviewed_by: "@claude-reviewer"
completion-commit: ef9c729485c072af6bf86afc83c07bca374613a9
---
# T0051: Restructure the README into bootstrap, build, install, command-line tools, and library sections linking to tool docs and tutorials

## Goals
Restructure `README.md` into five sections: Bootstrap, Build, Install, Command-line tools, and Library.
List each console script with its purpose and a link to its `docs/tools/` page.
List each library package group with its main uses and a link to its `docs/tutorials/` page.
Move remaining README-only tool details into the matching `docs/tools/` pages, and maintenance scripts into `docs/devops.md`.
Add a Tutorials group to `docs/index.md`, and bump the `-pre` patch version with a `CHANGELOG.md` entry.

## Task Execution Steps
- [x] **[Read]**      Read README.md, docs/index.md, docs/devops.md, and every docs/tools page.
- [x] **[Doc]**       Move README-only tool and maintenance-script details into docs/tools pages and docs/devops.md.
- [x] **[Doc]**       Rewrite README.md into the five sections with tool and tutorial link tables.
- [x] **[Doc]**       Group docs/index.md entries into Core, Tools, and Tutorials, and update CHANGELOG.md and pyproject.toml.
- [x] **[Verify]**    Run the completion check and confirm every README link resolves.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  Split from the 2026-11-10 README restructuring request; runs last, after T0050 and T0052 move the package sections.

- [2026-11-10] **[Doc]**
  Rewrote README.md into bootstrap, build, install, tool, and library sections; regrouped docs/index.md; moved maintenance scripts into docs/devops.md.
  - Dropped stale v1 wrapper scripts and the unverified --help/--version claim from devops.md.

- [2026-11-10] **[Decide]**
  Left docs/tools pages unchanged: every README-only tool detail was already there.

- [2026-11-10] **[Verify]**
  The completion check exited 0, and all five tools accept help, version, -h, --version, and --verbose.
  - Files touched: 4, plus the pyproject.toml bump by plan tasks stop.
  - Lines touched: 269.
  - Reopenings: 0.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 rejected by @claude-reviewer: README restructure is complete and lossless, but README.md:35 wrongly says all four global install commands use an isolated environment; two optional nits.
  - Findings: [review-findings-1.md](T0051-restructure-the-readme-into-bootstrap-build-install-command/review-findings-1.md).

- [2026-11-10] **[Implement]**
  Reworked review round 1: scoped the isolated-environment claim to pipx and uv tool, added net to Script utilities, and moved the migration guide link.

- [2026-11-10] **[Verify]**
  The completion check exits 0 after rework.

- [2026-11-10] **[Review]**
  Round 2 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 2 approved by @claude-reviewer: Round 1 findings F1, N1, and N2 are fixed; lint and task validation pass.
  - Findings: [review-findings-2.md](T0051-restructure-the-readme-into-bootstrap-build-install-command/review-findings-2.md).

- [2026-11-10] **[Complete]**
  Task completed successfully.

