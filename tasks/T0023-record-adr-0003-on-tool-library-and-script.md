---
id: T0023
owner: "@gemini"
session: antigravity-20261109-f012c8
needs: []
branch: task/T0023-record-adr-0003-on-tool-library-and-script
worktree: .plan/work/T0023-record-adr-0003-on-tool-library-and-script
status: active
started_at: "2026-11-09T18:59:04Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0023: Record ADR-0003 on tool, library, and script boundaries with shared CLI conventions, and open v2.0.0-pre

## Goals
Write `docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md` recording every decision in the technical spec.
Mark ADR-0001 as partially superseded by ADR-0003, keeping its unchanged parts in force.
Update `docs/requirements.md` and `docs/index.md` for the five standalone tools and the reusable devops scope.
Open v2.0.0-pre: rename the top `CHANGELOG.md` heading and set the `pyproject.toml` version to match.
Replace the stale pre-1.0 semver note in `CLAUDE.md`.

## Task Execution Steps
- [x] **[Read]**      Read ADR-0001, ADR-0002, docs/requirements.md, CHANGELOG.md, and this task's technical spec.
- [x] **[Implement]** Write ADR-0003 covering every decision listed in the technical spec.
- [x] **[Implement]** Mark ADR-0001 partially superseded, and update requirements, the docs index, and CLAUDE.md.
- [x] **[Implement]** Rename the v1.3.6-pre heading to v2.0.0-pre and set the matching pyproject.toml version.
- [x] **[Verify]**    Run the offline Markdown linter on changed documents and the full test suite.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User approved v2.0.0-pre, the five standalone tools, the uniform CLI conventions, and a library-based reusable devops on 2026-11-09.

- [2026-11-09] **[Implement]**
  Recorded ADR-0003, updated ADR-0001, docs, and CLAUDE.md, and opened v2.0.0-pre.

- [2026-11-09] **[Verify]**
  Verified offline Markdown linting on changed docs and full pytest suite.
  - Files touched: 7.
  - Lines touched: 248.
  - Reopenings: 0.

