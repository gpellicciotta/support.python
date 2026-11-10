### Problem
`ToolHarness.format_help` and `ToolHarness.format_action_help` pad option labels with a fixed `:<23` width.
A label of 23 or more characters runs into its description with no space.
A 22-character label keeps one space and breaks the column alignment, as `agent-files help` shows for `--manifest-source NAME`.

### Decisions
- **[Decided]** Widen the option column instead of wrapping the description to the next line.
  The Actions block already uses `max(longest + 2, 23)`, so options follow the same rule.
- **[Decided]** Compute one column width per help screen across standard, global, and action options.
  Standard option lines render at that width too, so the whole Options block stays aligned.
- **[Decided]** Keep the 23-column layout unchanged when every label is 21 characters or shorter.

### Declared Files
- src/support_python/cli.py
- tests/test_cli.py
- tests/tools/test_agent_files.py (two padded `agent-files help` assertions shift by one column)
- CHANGELOG.md

### Tests
- Unit: a global argument label of 30 characters keeps at least two spaces before its help in `format_help`, aligned with the standard options.
- Unit: an action option label of 30 characters keeps at least two spaces before its help in `format_action_help`, aligned with the standard options.
- Unit: short-label harnesses render options at column 25 exactly as before.
- Integration: installed `agent-files help` prints `--manifest-source NAME` with at least two spaces before its description, aligned with `--log-level LEVEL`.

Completion check: `.venv/Scripts/python -m pytest -q`, `.venv/Scripts/ruff check .`, plus the integration check above.
Size estimate: 3 files, 80 lines.
