### Declared Files
- src/support_python/devops.py
- tests/test_devops.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/requirements.md

Size estimate: 6 files, 280 lines

**[Estimation]** Based on adding fallback directory discovery in `resolve_cloud_sql_proxy_bin`, clean missing-Docker error handling in `CloudSqlProxyManager.start`, and unit/integration tests.

### Tests
- Unit: `resolve_cloud_sql_proxy_bin` finds `cloud-sql-proxy` in `~/bin` and `~/.local/bin` when absent from `PATH` and `repo_root`.
- Unit: `resolve_cloud_sql_proxy_bin` finds `cloud-sql-proxy` in the Google Cloud SDK `bin` directory adjacent to `gcloud` or under `LOCALAPPDATA`.
- Unit: `resolve_cloud_sql_proxy_bin` ignores legacy v1 `cloud_sql_proxy` / `cloud_sql_proxy.exe` binaries.
- Unit: `resolve_cloud_sql_proxy_bin` returns `None` when absent from `PATH`, `repo_root`, and all fallback directories.
- Unit: `CloudSqlProxyManager.start` fails cleanly (logs an error and returns `1` without calling `subprocess.run`) when both `cloud-sql-proxy` and `docker` are missing.
- Unit: `CloudSqlProxyManager.start` catches `OSError` when launching the proxy command fails, logs an error, and returns `1`.
- Integration: `CloudSqlProxyManager.start` discovers a proxy executable installed in a non-`PATH` `~/bin` directory and executes it end-to-end.

Completion check: python -m pytest && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Search `PATH`, `repo_root`, user bin dirs (`~/bin`, `~/.local/bin`), and Google Cloud SDK `bin` dirs for v2 `cloud-sql-proxy` binaries only.
- **[Decided]** Check `shutil.which("docker")` before the Docker fallback in `CloudSqlProxyManager.start` and catch `OSError` around `subprocess.run`, returning `1`.
- **[Decided]** Keep the package version and top changelog heading at `v1.0.11-pre`.
