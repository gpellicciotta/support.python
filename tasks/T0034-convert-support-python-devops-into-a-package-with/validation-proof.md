## Walkthrough & Validation
### Summary of Changes
- Converted `src/support_python/devops.py` into the `support_python.devops` package (`__init__.py`, `steps.py`, and `services.py`).
- Extracted `EXIT_COMMAND_NOT_FOUND`, `resolve_executable`, `stream_subprocess`, `run_step_command`, and `run_step` into `src/support_python/devops/steps.py`.
- Kept `_candidate_cloud_sql_proxy_dirs`, `resolve_cloud_sql_proxy_bin`, `CloudSqlProxyManager`, `LocalDockerManager`, `LocalMySqlManager`, `LocalServerManager`, `LocalMailManager`, and `LocalVerifier` in `src/support_python/devops/services.py`.
- Re-exported all 12 pre-split `__all__` symbols in `src/support_python/devops/__init__.py` and updated test patch targets in `tests/test_devops.py` and `tests/test_streaming.py`.

### Red-Phase Test Failure Proof
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest -q tests/test_devops.py -k DevopsPackageExportsTests`
Exit code: `1`
```text
F                                                                        [100%]
================================== FAILURES ===================================
_ DevopsPackageExportsTests.test_pre_split_public_names_import_from_devops_and_submodules _

self = <test_devops.DevopsPackageExportsTests testMethod=test_pre_split_public_names_import_from_devops_and_submodules>

    def test_pre_split_public_names_import_from_devops_and_submodules(self) -> None:
        import support_python.devops as devops_pkg
        from support_python.devops import (
            EXIT_COMMAND_NOT_FOUND,
            CloudSqlProxyManager,
            LocalDockerManager,
            LocalMailManager,
            LocalMySqlManager,
            LocalServerManager,
            LocalVerifier,
            resolve_cloud_sql_proxy_bin,
            resolve_executable,
            run_step,
            run_step_command,
            stream_subprocess,
        )
>       from support_python.devops import services, steps
E       ImportError: cannot import name 'services' from 'support_python.devops' (C:\Dev-Projects\support.python\.plan\work\T0034-convert-support-python-devops-into-a-package-with\src\support_python\devops.py)

tests\test_devops.py:43: ImportError
=========================== short test summary info ===========================
FAILED tests/test_devops.py::DevopsPackageExportsTests::test_pre_split_public_names_import_from_devops_and_submodules
1 failed, 47 deselected in 0.80s
```

### Green-Phase Test Suite Proof
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest -q`
Exit code: `0`
```text
............................................................ [  8%]
.............................................................. [ 16%]
................................................ [ 23%]
........................................................ [ 30%]
........................................................................ [ 40%]
.................................s...................................... [ 50%]
..............................................s......s.................. [ 59%]
........................................................................ [ 69%]
...................................................................... [ 79%]
........................................................................ [ 88%]
........................................................................ [ 98%]
..........                                                               [100%]
735 passed, 3 skipped, 64 subtests passed in 150.38s (0:02:30)
```

### Sibling Consumer Integration Proof
Command: `$env:PYTHONPATH = "src"; C:\Dev-Projects\support.python\.venv\Scripts\python.exe C:\Dev-Projects\auth\scripts\devops.py --help`
Exit code: `0`
```text
usage: devops.py [-h] [--port PORT] [--mysql-port MYSQL_PORT]
                 [--env-file ENV_FILE] [--mysql-env-file MYSQL_ENV_FILE]
                 [--log-file LOG_FILE] [--memory-db] [--build] [--verify]
                 [--anonymized] [--app-name APP_NAME] [--background]
                 [--keep-db] [--verbose] [--debug] [--version]
                 {docker,db,server,client,mail,production,start,stop,test-emails,status,verify,verify-anonymized,proxy,verify-deployment,versions,set-versions,help,version}
                 ...

Unified local development operations and environment manager for Auth
[... 46 lines omitted ...]
  --verbose, -v         Enable verbose log output
  --debug               Enable debug log output
  --version             Show project version and exit
```

### Linter and Formatting Proof
Command: `C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe check .; C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe format --check .`
Exit code: `0`
```text
All checks passed!
100 files already formatted
```
