# T0003 Validation Proof

## Walkthrough & Validation
Command: `python -m pytest tests/test_processes.py` (exit code 1, red phase before implementation)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0003-add-process-hierarchy-and-safe-termination-helpers
configfile: pyproject.toml
collected 0 items / 1 error

=================================== ERRORS ====================================
__________________ ERROR collecting tests/test_processes.py ___________________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0003-add-process-hierarchy-and-safe-termination-helpers\tests\test_processes.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_processes.py:16: in <module>
    from support_python import (
E   ImportError: cannot import name 'get_process_hierarchy' from 'support_python' (C:\Dev-Projects\support.python\.plan\work\T0003-add-process-hierarchy-and-safe-termination-helpers\src\support_python\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_processes.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.87s ===============================
```

Command: `python -m pytest tests/test_processes.py` (exit code 0, green phase after implementation)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0003-add-process-hierarchy-and-safe-termination-helpers
configfile: pyproject.toml
collected 27 items

tests\test_processes.py ...........................                      [100%]

============================= 27 passed in 0.97s ==============================
```

Command: `python -m pytest` (exit code 0, full test suite; background task `08d0e3bc-16b0-4d72-988c-d296161c4859/task-105`)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0003-add-process-hierarchy-and-safe-termination-helpers
configfile: pyproject.toml
testpaths: tests
collected 482 items

tests\test_backup_git_repos.py ......................................... [  8%]
...........................................................              [ 20%]
tests\test_capture.py .........................                          [ 25%]
tests\test_cli.py .............                                          [ 28%]
tests\test_crypto.py .....                                               [ 29%]
tests\test_dates.py .............                                        [ 32%]
tests\test_devops.py .......................................             [ 40%]
tests\test_env.py ..                                                     [ 40%]
tests\test_errors.py ..........                                          [ 42%]
tests\test_extract_release_notes.py ....                                 [ 43%]
tests\test_git.py ...........................................            [ 52%]
tests\test_httpd.py .                                                    [ 52%]
tests\test_install_from_github_release.py .............                  [ 55%]
tests\test_kill_processes.py ...........................                 [ 61%]
tests\test_locking.py ..........                                         [ 63%]
tests\test_locking_mysql.py .........s                                   [ 65%]
tests\test_locking_redis.py ......s                                      [ 66%]
tests\test_logging.py ...................                                [ 70%]
tests\test_migrate_namespace.py ....                                     [ 71%]
tests\test_models.py ...................                                 [ 75%]
tests\test_net.py ................                                       [ 78%]
tests\test_processes.py ...........................                      [ 84%]
tests\test_sql.py ..............                                         [ 87%]
tests\test_tables.py .........                                           [ 89%]
tests\test_terminal.py .                                                 [ 89%]
tests\test_tokens.py .....                                               [ 90%]
tests\test_tool_common.py ......................................         [ 98%]
tests\test_version.py ........                                           [100%]

================= 480 passed, 2 skipped in 157.96s (0:02:37) ==================
```

Command: `ruff check .` (exit code 0)

```text
All checks passed!
```

Command: `ruff format --check .` (exit code 0)

```text
69 files already formatted
```
