### Declared Files
- src/support_python/locking.py
- tests/test_locking_redis.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 8 files, 350 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: With a fake client, acquire sends SET key token NX PX ttl; a held key makes acquire retry until the timeout.
- Unit: release runs the Lua script only for the holder's token; a different token leaves the key.
- Unit: Re-entrant acquire in one thread does not issue a second SET.
- Unit: Constructing the lock with the redis package missing raises ImportError that names the 'redis' extra (patched sys.modules).
- Unit: The factory returns RedisLock for redis:// and rediss:// URLs.
- Integration: Against a live Redis server: two processes contend for one key; only one holds it at a time, and a crashed holder's lease expires after the TTL. Runs when SUPPORT_PYTHON_TEST_REDIS_URL is set and is reported as skipped otherwise.

Completion check: python -m pytest tests/test_locking_redis.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** The redis package goes in an optional-dependencies extra named redis, never in core dependencies.
- **[Decided]** Live-server tests skip without the environment variable, so CI without Redis stays green; the skip is visible in the pytest report. A fake-client suite always runs.
- **[Decided]** pyproject.toml is a counted file in addition to the declared list.
