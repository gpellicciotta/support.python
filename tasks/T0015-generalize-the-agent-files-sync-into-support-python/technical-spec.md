### Declared Files
- src/support_python/agent_files.py
- src/support_python/cli.py
- tests/test_agent_files.py
- CHANGELOG.md

### Tests
- Unit: all cases from dev-guidelines `test_update_global_agent_files.py` pass against `support_python.agent_files`.
- Integration: `support-python agent-files sync --dry-run` run from dev-guidelines yields the same diff as the original script.

Completion check: `python -m pytest tests/test_agent_files.py -q`
