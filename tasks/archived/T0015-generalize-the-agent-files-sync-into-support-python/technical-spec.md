### Declared Files
- src/support_python/agent_files.py
- src/support_python/cli.py
- tests/test_agent_files.py
- README.md
- docs/index.md
- pyproject.toml
- CHANGELOG.md

### Tests
- Unit: all cases from dev-guidelines `test_update_global_agent_files.py` pass against `support_python.agent_files`.
- Integration: `support-python agent-files sync --dry-run` run from dev-guidelines yields the same diff as the original script.

Completion check: `python -m pytest tests/test_agent_files.py -q`
Size estimate: 7 files, 2450 lines
Size note: Above the typical line in raw diff because two files are mechanical copies of dev-guidelines update-global-agent-files.py (1,024 lines) and test_update_global_agent_files.py (1,254 lines); hand-written changes are 243 lines across 7 files.
