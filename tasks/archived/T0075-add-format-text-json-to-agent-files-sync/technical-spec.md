### Declared Files
- src/support_python/tools/agent_files.py
- tests/tools/test_agent_files.py
- docs/tools/agent-files.md
- CHANGELOG.md

### Tests
- Unit: `sync --format json` lists each written skill and the instruction-file status per tool.
- Unit: `sync --dry-run --format json` matches `check --format json` for the same tree.
- Integration: Run the installed `agent-files sync --format json` against temporary target files and parse `stdout`.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_agent_files.py` plus the integration scenario above.
Size estimate: 4 files, 200 lines

### Notes
- Name JSON fields in lowercase kebab-case, consistent with the tool's existing JSON documents.
- Treat every field as a compatibility contract; T0081 later specifies the documents.
- Follow [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md).
