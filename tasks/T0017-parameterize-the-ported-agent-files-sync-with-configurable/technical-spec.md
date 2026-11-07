### Declared Files
- src/support_python/agent_files.py
- src/support_python/agent_files_config.py
- tests/test_agent_files.py
- docs/agent-files.md
- CHANGELOG.md
- pyproject.toml

### Tests
- Unit: config loading covers defaults, overrides, a missing file, and an invalid schema.
- Unit: a second fixture project with another marker and manifest source syncs without touching dev-guidelines blocks.
- Unit: an added registry entry is listed and synced like the built-in tools.
- Integration: `support-python agent-files sync --dry-run --config {{dev-guidelines}}/agent-files.json` reports no diff against current global files.

Completion check: `python -m pytest tests -q`
Size estimate: 5 files, 300 lines.
Size note: 6 files and 731 lines because agent_files_config.py, CLI flags, multi-project marker/manifest tests, and docs/agent-files.md must land together for a verifiable parameterization.
