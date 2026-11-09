### Declared Files
- src/support_python/ratelimit.py
- tests/test_ratelimit.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 7 files, 150 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: max_tasks_per_hour None or <= 0 disables limiting: can_dispatch is True and wait is 0.0.
- Unit: With a cap of 2, two recorded dispatches block the third and allow it again once the oldest leaves the window.
- Unit: prune drops timestamps at or before now - window_seconds and keeps newer ones.
- Unit: get_wait_duration returns oldest + window - now, with a 1.0 second minimum when blocked.
- Unit: A custom window_seconds changes the window.
- Integration: Drive a limiter through a simulated hour with injected timestamps: record, block, wait, and reallow, asserting each decision.

Completion check: python -m pytest tests/test_ratelimit.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Keep the class name and method names for a drop-in migration of plan.
- **[Decided]** All methods accept an injected 'now' so tests need no sleeping.
