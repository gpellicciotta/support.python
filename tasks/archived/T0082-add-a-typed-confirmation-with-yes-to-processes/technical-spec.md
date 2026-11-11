### Declared Files
- src/support_python/tools/processes.py
- tests/tools/test_processes.py
- docs/tools/processes.md
- CHANGELOG.md

### Tests
- Unit: `kill` with confirmation enabled and no `--yes` terminates nothing when the typed answer does not match.
- Unit: `kill --yes` and `kill --dry-run` never prompt.
- Integration: Run the installed `processes kill {{pid}} --yes` on a child Python process and confirm it exits.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_processes.py` plus the integration scenario above.
Size estimate: 4 files, 150 lines

### Notes
- On 2026-11-10 the user stated that `processes kill` is exempt from the general `--yes` rule; this task revisits that.
- Agent guidelines call `processes kill {{pid}}` non-interactively; any prompt must not block them.
- Follow [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md) and [process-management-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/process-management-guidelines.md).
