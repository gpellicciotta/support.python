---
id: T0055
owner: "@claude-code"
needs: []
branch: —
worktree: —
status: completed
started_at: "2026-11-10T10:09:57Z"
ended_at: "2026-11-10T10:15:40Z"
review: agent
preview: none
protocol: adhoc
review_status: approved
review_round: 1
reviewed_by: "@claude-code-subagent"
completion-commit: 89e6a9d69391032bb3489e8d8f5df4fac40bca72
---
# T0055: Make --debug imply --verbose in ToolHarness, so actions reading args.verbose also see it

## Goals
The dev-guidelines [CLI Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md) now say `--debug` sets the `DEBUG` threshold and implies `--verbose`.
`CliLogger` already sets `verbose = verbose or debug`, but `ToolHarness` leaves `args.verbose` false under `--debug`.
Actions that read `args.verbose` directly therefore ignore `--debug`.

Specifications: [technical-spec.md](T0055-make-debug-imply-verbose-in-toolharness-so-actions/technical-spec.md).
Completion check: `python -m pytest tests/test_cli.py` and `ruff check src tests`
Size estimate: 5 files, 80 lines

## Task Execution Steps
- [x] **[Verify]**    Author the failing unit tests from the technical spec and record their failure output.
- [x] **[Implement]** Set `args.verbose` whenever `--debug` is given, before `ToolHarness` dispatches any action.
- [x] **[Verify]**    Run the completion check and the integration scenario; record verbatim output.
- [x] **[Doc]**       Update the CLI docs mentioning `--debug` and CHANGELOG.md.
- [x] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Verify]**
  Red phase failed four new tests; full suite, ruff, and lint-markdown --debug integration pass.
  - Undeclared: git_repository_backup.py hand-written --debug help line.

- [2026-11-10] **[Review]**
  Round 1 requested (mode: agent).

- [2026-11-10] **[Review]**
  Round 1 approved by @claude-code-subagent.

- [2026-11-10] **[Review]**
  Agent reviewer approved; applied nits: moved __main__ blocks last, wrapped requirements line, added lint-markdown --debug test.
  - Undeclared: tests/test_logging.py, tests/tools/test_lint_markdown.py.

- [2026-11-10] **[Verify]**
  Recorded task outcomes.
  - Files touched: 8.
  - Lines touched: 95.
  - Reopenings: 0.

- [2026-11-10] **[Complete]**
  Task completed successfully.

