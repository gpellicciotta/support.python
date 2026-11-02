---
id: T0004
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0004: Add duration and time formatting helpers

## Goals
Add duration and time formatting helpers to support_python, extracted from the plan project's `utils/dates.py`. Scope: parse_iso8601, parse_date_or_datetime, parse_duration_to_seconds, format_duration, format_short_duration, format_epoch, format_past_epoch. Out of scope: extract_reset_time_from_text and extract_rate_limit_reset, which are agent-specific. Do not shadow the existing dates.format_datetime.

## Task Execution Steps
- [ ] **[Read]**      Read plan's utils/dates.py and this repo's dates.py; list name and behavior collisions, such as format_datetime.
- [ ] **[Implement]** Author the unit and integration tests listed in the technical specification.
- [ ] **[Verify]**    Run the new tests and confirm they fail before implementation.
- [ ] **[Implement]** Implement durations.py and re-export its public symbols from the package root.
- [ ] **[Verify]**    Run pytest, ruff check, and ruff format --check until all pass.
- [ ] **[Doc]**       Update CHANGELOG.md, README.md, CLAUDE.md architecture list, and docs/index.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-10-31] **[Doc]**
  Companion task file scaffolded at task creation.
