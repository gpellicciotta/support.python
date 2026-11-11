### Declared Files
- src/support_python/tools/agent_digest.py
- tests/tools/test_agent_digest.py
- docs/tools/agent-digest.md
- CHANGELOG.md

### Tests
- Unit: A GitHub URL ending in `/docs/guidelines/plan-task-usage-guidelines.md` becomes ``the `plan-task-usage-guidelines` skill`` in a derived skill.
- Integration: Run `agent-digest generate` on a guideline linking both URL forms, and `check` reports it up to date.

Completion check: `pytest tests/tools/test_agent_digest.py` and `ruff check src tests`
Size estimate: 4 files, 60 lines
