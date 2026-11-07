### Declared Files
- src/support_python/processes.py
- tests/test_processes.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md
- pyproject.toml

Size estimate: 7 files, 450 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: get_process_hierarchy(os.getpid()) contains the current PID and its parent PID.
- Unit: terminate_process raises ValueError for PIDs <= 0.
- Unit: terminate_process builds taskkill [/F] on win32 and sends SIGTERM or SIGKILL elsewhere (patched sys.platform, subprocess.run, os.kill).
- Unit: terminate_process_tree returns False for PIDs <= 0 and for failures, and uses taskkill /F /T on win32.
- Unit: safe_kill skips the current PID and every ancestor with a warning, and reports failures through its return value.
- Unit: is_process_alive is True for the current PID, False for a dead PID, and False when expected_start differs beyond slack_seconds.
- Integration: Start a child Python process that sleeps; assert is_process_alive; end it with terminate_process_tree; assert it is gone within a timeout. The test uses no raw kill calls except through the function under test.

Completion check: python -m pytest tests/test_processes.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** No psutil dependency; the library stays stdlib-only. Use psutil only if the reconciled code already needs it, and then as a lazy optional import.
- **[Decided]** safe_kill keeps its ancestor-protection guard; terminate_process stays unguarded and documents that callers must protect ancestors.
- **[Decided]** Pointing scripts/kill-processes.py (and the sibling copies) at the library is a follow-up task, not part of this one.
- **[Decided]** Added pyproject.toml to synchronize the changelog version, bringing the declared count to eight files.

Size note: Comprehensive docstrings and unit and integration tests for all seven process helpers exceed 400 lines within one subsystem.
