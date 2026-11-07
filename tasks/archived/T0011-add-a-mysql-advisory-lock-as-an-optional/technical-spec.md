### Declared Files
- src/support_python/locking.py
- tests/test_locking_mysql.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 8 files, 400 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: With a fake connection, acquire runs SELECT GET_LOCK(name, timeout); result 1 acquires, 0 times out, NULL raises an error.
- Unit: release runs SELECT RELEASE_LOCK(name) and tolerates a result of 0.
- Unit: URL parsing handles user, password, host, port, and database for all three schemes.
- Unit: Constructing the lock with pymysql missing raises ImportError that names the 'mysql' extra (patched sys.modules).
- Unit: The connection is closed after release and on acquire failure.
- Integration: Against a live MySQL server: two processes contend for one lock name; only one holds it at a time, and the lock frees when the holder's connection closes. Runs when SUPPORT_PYTHON_TEST_MYSQL_URL is set and is reported as skipped otherwise.

Completion check: python -m pytest tests/test_locking_mysql.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** The pymysql package goes in an optional-dependencies extra named mysql, never in core dependencies.
- **[Decided]** Live-server tests skip without the environment variable, so CI without MySQL stays green; the skip is visible in the pytest report. A fake-connection suite always runs.
- **[Decided]** pyproject.toml is a counted file in addition to the declared list.
