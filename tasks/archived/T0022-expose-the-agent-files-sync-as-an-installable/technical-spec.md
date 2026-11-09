### Declared Files
- pyproject.toml
- src/support_python/agent_files.py
- tests/test_agent_files.py
- tests/test_agent_files_script.py
- docs/agent-files.md
- README.md
- CHANGELOG.md

### Tests
- Unit: `importlib.metadata.entry_points(group="console_scripts")` holds `agent-files` with value `support_python.agent_files:main`.
- Unit: `agent-files version` output starts with `agent-files v`, and usage errors name `agent-files`.
- Integration: in a fresh virtual environment with the package installed, `agent-files list` and `agent-files sync --dry-run` run from dev-guidelines and exit 0.

Completion check: `python -m pytest tests -q`, plus the integration commands above.
Size estimate: 7 files, 60 lines.
