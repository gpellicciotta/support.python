### Changes
- `ToolHarness.run` calls `support_python.terminal.configure_utf8_output()` once, before argument parsing.
- Delete the `sys.stdout.reconfigure`/`sys.stderr.reconfigure` blocks in `tools/agent_files.py`,
  `tools/git_repository_backup.py`, and `tools/lint_markdown.py`, and the explicit call in `tools/processes.py`.
- Keep `configure_utf8_output` public; leave the stream handling inside `CliLogger` alone unless it duplicates this.
- Delete the `ToolLogger` and `TeeLogger` aliases from `logging.py`, `__all__`, and `support_python/__init__.py`.

Mechanical command: `git grep -lwE "ToolLogger|TeeLogger" -- src tests | xargs sed -i -E "s/\b(ToolLogger|TeeLogger)\b/CliLogger/g"`
- Fix duplicate imports the sweep creates by hand; that fix-up belongs to this task.

### Declared Files
- src/support_python/cli.py
- src/support_python/logging.py
- src/support_python/__init__.py
- src/support_python/processes.py
- src/support_python/tools/agent_files.py
- src/support_python/tools/git_repository_backup.py
- src/support_python/tools/lint_markdown.py
- src/support_python/tools/processes.py
- tests/test_cli.py
- tests/test_logging.py
- tests/tools/test_agent_files.py
- tests/tools/test_git_repository_backup.py
- tests/tools/test_lint_markdown.py
- CLAUDE.md
- docs/index.md
- README.md
- CHANGELOG.md

### Tests
- Unit: `ToolHarness.run` calls `configure_utf8_output` exactly once before dispatching any action.
- Unit: neither `support_python.logging` nor `support_python` exposes `ToolLogger` or `TeeLogger`.
- Unit: no module under `src/support_python/tools/` calls `reconfigure(` (source scan).
- Integration: installed `processes help`, `agent-files help`, `lint-markdown help`, and `git-repository-backup help`
  exit 0 with output piped through a subprocess, printing a non-ASCII character without `UnicodeEncodeError`
  (implemented via `python -c` invoking each tool module's `main(['help'])` followed by a non-ASCII print under a `PYTHONIOENCODING=cp1252` pipe so both `help` and non-ASCII emission share the same reconfigured process stream).

Completion check: `.venv/Scripts/ruff check .` and `.venv/Scripts/python -m pytest -q`, plus the integration commands above.
Size estimate: 11 files, 150 lines.
Size note: above 8 files because each tool loses a duplicated block and the alias sweep touches additional module, test, and doc files (17 total files, 267 lines); total hand-written lines stay small.
