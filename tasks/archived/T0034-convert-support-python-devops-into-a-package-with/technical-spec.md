### Module Split
- `devops/steps.py`: `resolve_executable`, `stream_subprocess`, `run_step_command`, `run_step`, `EXIT_COMMAND_NOT_FOUND`,
  and the private helpers they use.
- `devops/services.py`: `_candidate_cloud_sql_proxy_dirs`, `resolve_cloud_sql_proxy_bin`, `CloudSqlProxyManager`,
  `LocalDockerManager`, `LocalMySqlManager`, `LocalServerManager`, `LocalMailManager`, and `LocalVerifier`.
- `devops/__init__.py`: re-exports every name in the current `support_python.devops.__all__`.

Mechanical command: `git mv src/support_python/devops.py src/support_python/devops/services.py`, then move the step helpers by hand into `steps.py`.

### Declared Files
- src/support_python/devops/__init__.py
- src/support_python/devops/steps.py
- src/support_python/devops/services.py
- tests/test_devops.py
- tests/test_streaming.py
- CLAUDE.md
- CHANGELOG.md

### Tests
- Unit: every name in the pre-split `__all__`, listed explicitly in the test, imports from `support_python.devops`.
- Unit: the existing devops and streaming suites pass with patch targets moved to `devops.steps` or `devops.services`.
- Integration: with this checkout's `src` on `PYTHONPATH`, `python ../auth/scripts/devops.py --help` exits 0
  (read-only use of a sibling consumer); waive with the reason if auth needs unavailable dependencies.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration command above.
Size estimate: 7 files, 500 lines.
