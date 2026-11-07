### Declared Files
- src/support_python/agent_files.py
- src/support_python/agent_files_config.py
- tests/test_agent_files.py
- docs/agent-files.md
- CHANGELOG.md

### Tests
- Unit: config loading covers defaults, overrides, a missing file, and an invalid schema.
- Unit: a second fixture project with another marker and manifest source syncs without touching dev-guidelines blocks.
- Unit: an added registry entry is listed and synced like the built-in tools.
- Integration: `support-python agent-files sync --dry-run --config {{dev-guidelines}}/agent-files.json` reports no diff against current global files.

Completion check: `python -m pytest tests -q`
