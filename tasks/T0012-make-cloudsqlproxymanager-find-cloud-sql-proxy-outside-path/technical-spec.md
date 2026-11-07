### Declared Files
- src/support_python/devops.py
- tests/test_devops.py
- CHANGELOG.md
- README.md
- pyproject.toml

Size estimate: 5 files, 280 lines

**[Estimation]** Based on adding fallback directory discovery in `resolve_cloud_sql_proxy_bin`, clean missing-Docker error handling in `CloudSqlProxyManager.start`, and unit/integration tests.

### Tests
- Unit: `resolve_cloud_sql_proxy_bin` resolves `CLOUD_SQL_PROXY_BIN` when set to an existing executable file.
- Unit: `resolve_cloud_sql_proxy_bin` finds `cloud-sql-proxy` in `~/bin` and `~/.local/bin` when absent from `PATH` and `repo_root`.
- Unit: `resolve_cloud_sql_proxy_bin` finds `cloud-sql-proxy` in the Google Cloud SDK `bin` directory adjacent to `gcloud` or under `LOCALAPPDATA`.
- Unit: `resolve_cloud_sql_proxy_bin` returns `None` when absent from `PATH`, `repo_root`, and all fallback directories.
- Unit: `CloudSqlProxyManager.start` fails cleanly (logs an error and returns `1` without calling `subprocess.run`) when both `cloud-sql-proxy` and `docker` are missing.
- Unit: `CloudSqlProxyManager.start` catches `OSError` when launching the proxy command fails, logs an error, and returns `1`.
- Integration: `CloudSqlProxyManager.start` discovers a proxy executable installed in a non-`PATH` `~/bin` directory and executes it end-to-end.

Completion check: python -m pytest tests/test_devops.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Search `CLOUD_SQL_PROXY_BIN`, `PATH`, `repo_root`, user bin dirs (`~/bin`, `~/.local/bin`), and Google Cloud SDK `bin` dirs.
- **[Decided]** Check `shutil.which("docker")` before the Docker fallback in `CloudSqlProxyManager.start` and catch `OSError` around `subprocess.run`, returning `1`.
