### Declared Files
- src/support_python/tools/agent_digest.py
- tests/tools/test_agent_digest.py
- docs/tools/agent-digest.md
- CHANGELOG.md

### Tests
- Unit: `generate --format json` reports each written file with its status and the digest byte size.
- Unit: `generate --dry-run --format json` reports planned statuses and writes nothing.
- Integration: Run the installed `agent-digest generate tests/fixtures/agent_digest/guidelines --format json` into a temporary directory.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_agent_digest.py` plus the integration scenario above.
Size estimate: 4 files, 200 lines

### Notes
- Name JSON fields in lowercase kebab-case, consistent with the tool's existing JSON documents.
- Treat every field as a compatibility contract; T0081 later specifies the documents.
- Follow [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md).
