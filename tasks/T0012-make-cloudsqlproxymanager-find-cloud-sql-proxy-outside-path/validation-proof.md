## Walkthrough & Validation

### Red-Phase Test Failure (Before Implementation)
Command: `python -m pytest tests/test_devops.py -q -k "ResolveCloudSqlProxyBinTests or CloudSqlProxyManagerTests" --tb=short` (exit code 1)
```text
FFF.FF.F..FF.F..                                                         [100%]
================================== FAILURES ===================================
FAILED tests/test_devops.py::ResolveCloudSqlProxyBinTests::test_finds_proxy_from_env_var
FAILED tests/test_devops.py::ResolveCloudSqlProxyBinTests::test_finds_proxy_in_local_bin_outside_path
FAILED tests/test_devops.py::ResolveCloudSqlProxyBinTests::test_finds_proxy_in_localappdata_cloud_sdk_outside_path
FAILED tests/test_devops.py::ResolveCloudSqlProxyBinTests::test_finds_proxy_in_user_bin_outside_path
FAILED tests/test_devops.py::ResolveCloudSqlProxyBinTests::test_finds_proxy_next_to_gcloud_outside_path
FAILED tests/test_devops.py::ResolveCloudSqlProxyBinTests::test_returns_none_when_not_found
FAILED tests/test_devops.py::CloudSqlProxyManagerTests::test_start_fails_cleanly_when_proxy_and_docker_missing
FAILED tests/test_devops.py::CloudSqlProxyManagerTests::test_start_fails_cleanly_when_subprocess_raises_oserror
FAILED tests/test_devops.py::CloudSqlProxyManagerTests::test_start_finds_and_executes_proxy_outside_path_integration
9 failed, 7 passed, 31 deselected in 1.37s
```

### Green-Phase Test Suite (After Implementation)
Command: `python -m pytest tests/test_devops.py tests/test_version.py tests/test_cli.py -q` (exit code 0)
```text
....................................................................     [100%]
68 passed in 2.03s
```

### Linter and Formatter Verification
Command: `ruff check . ; ruff format --check .` (exit code 0)
```text
All checks passed!
73 files already formatted
```

### Live Smoke Verification Outside PATH and Without Docker
Command: `python -c "import os, sys; sys.path.insert(0, 'src'); from support_python.devops import resolve_cloud_sql_proxy_bin, CloudSqlProxyManager; os.environ['PATH'] = ''; print('resolved outside PATH:', resolve_cloud_sql_proxy_bin()); mgr = CloudSqlProxyManager('proj:reg:inst'); mgr.resolve_proxy_bin = lambda: None; print('missing docker exit code:', mgr.start())"` (exit code 0)
```text
**[ERROR]** <devops> Local cloud-sql-proxy binary not found and Docker is not installed. Install cloud-sql-proxy or Docker to start the proxy.
resolved outside PATH: C:\Users\giova\bin\cloud-sql-proxy.exe
missing docker exit code: 1
```
