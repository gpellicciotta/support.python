### Command-Line Interface
```text
devops docker status | start
devops db status | start | stop
devops db snapshot [--source cloudsql|local|file] [--file PATH] [--load-target TARGET]
devops db load-snapshot [--file PATH] [--target TARGET]
devops db proxy [proxy options]
devops server status | stop
devops server start [--background] [--force-build] [--memory-db]
devops mail test-emails --to ADDRESS
devops client verify
devops client verify-deployment [--url URL]
```
- Copy option names, defaults, and help texts from `../auth/scripts/devops.py` (around lines 1841-1923), a read-only reference.
- Take the database target choices from `db_targets`, covering the counters.server and todos.server variants.

### API
```python
DevopsCli.add_services(
    *,
    docker: LocalDockerManager | None = None,
    mysql: LocalMySqlManager | None = None,
    proxy: CloudSqlProxyManager | None = None,
    server: LocalServerManager | None = None,
    mail: LocalMailManager | None = None,
    verifier: LocalVerifier | None = None,
    db_targets: Sequence[str] = ("local", "testdb"),
) -> None
```
- A group is registered only when its manager is supplied; `db proxy` needs `proxy`, and `db snapshot` needs `mysql`.
- Implement sub-actions as a positional choice on the group action; an unknown sub-action exits 2.
- Extend `ToolHarness` only if unavoidable, and then declare `src/support_python/cli.py` in the Execution Log.

### Declared Files
- src/support_python/devops/service_actions.py
- src/support_python/devops/cli.py
- src/support_python/devops/__init__.py
- tests/test_devops_service_actions.py
- README.md
- CHANGELOG.md

### Tests
- Unit: each sub-action calls the matching manager method with the parsed options (mocked managers).
- Unit: groups are absent when their manager is not supplied; an unknown sub-action exits 2.
- Integration: a `DevopsCli` with a real `LocalDockerManager` runs `docker status` and exits 0 or 1 with a status line, starting nothing.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration check above.
Size estimate: 6 files, 650 lines.
Size note: the groups share one registration and dispatch mechanism; splitting per group would duplicate that plumbing.
