---
id: T0056
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T10:15:47Z"
ended_at: "2026-11-10T10:24:09Z"
review: agent
preview: none
protocol: adhoc
review_status: approved
review_round: 1
reviewed_by: "@claude-code-subagent"
completion-commit: 5295895d84219946bb1845ccbb952b65007535f3
---
# T0056: Accept millisecond and offset instants and add date-only helpers in support_python.dates, per the REST API guidelines

## Goals
The dev-guidelines [REST API Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/rest-api-guidelines.md#dates-and-times) let servers send millisecond instants and clients send any UTC offset.
`support_python.dates` parses only `yyyy-MM-dd'T'HH:mm:ss'Z'`, so it rejects todos.server edit times such as `2026-11-06T10:15:30.123Z`.
It also lacks helpers for the `YYYY-MM-DD` date-only values the guidelines define.

Specifications: [technical-spec.md](T0056-accept-millisecond-and-offset-instants-and-add-date/technical-spec.md).
Completion check: `python -m pytest tests/test_dates.py tests/test_models.py` and `ruff check src tests`
Size estimate: 6 files, 200 lines

## Task Execution Steps
- [x] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [x] **[Implement]** Extend `parse_datetime` to accept milliseconds and UTC offsets, keeping Python 3.9 support.
- [x] **[Implement]** Add a `millis` option to `format_datetime`, and add `parse_date` and `format_date`.
- [x] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [x] **[Doc]**       Update `docs/requirements.md`, the REST client tutorial, and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Decide]**
  Empty strings parse to None in parse_date, mirroring parse_datetime; datetime inputs raise TypeError in parse_date and format_date.

- [2026-11-10] **[Verify]**
  Red phase failed on missing helpers; full suite, ruff, and Python 3.9 date/model tests pass.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-subagent.

- [2026-11-10] **[Review]**
  Agent reviewer approved; mapped offset OverflowError to ValueError test-first, documented stricter parsing, added edge tests.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 7.
  - Lines touched: 231.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

