### Declared Files
- src/support_python/locking.py
- tests/test_locking.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 7 files, 450 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: FileLock acquire and release; is_locked reflects state; the context manager acquires and releases.
- Unit: A second FileLock on the same path times out within the timeout and follows the source contract (False or LockTimeoutError).
- Unit: FileLock is re-entrant within one thread and counts nested acquires.
- Unit: NullLock always acquires.
- Unit: The factory returns NullLock for 'null'/'none', FileLock for 'file'/'local' or empty, and raises ValueError for unsupported schemes.
- Unit: For redis and mysql URLs the factory raises a clear error until T0010 and T0011 land.
- Integration: Two subprocesses contend for one FileLock path and write enter and exit markers to a file; markers never interleave.

Completion check: python -m pytest tests/test_locking.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Split from the original single locking request: Redis (T0010) and MySQL (T0011) are separate tasks to stay below the large size line; the three together exceed it.
- **[Decided]** The factory takes explicit arguments (backend, key, path, timeout) instead of plan's resolve_setting and .env fallback.
- **[Decided]** Timeouts accept seconds as a float; no dependency on T0004.
