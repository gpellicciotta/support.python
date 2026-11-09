### Red Phase: Failing Tests Before Implementation

Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/test_ratelimit.py`
Exit code: `1`
```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0008-add-a-task-rate-limiter
configfile: pyproject.toml
collected 0 items / 1 error

=================================== ERRORS ====================================
__________________ ERROR collecting tests/test_ratelimit.py ___________________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0008-add-a-task-rate-limiter\tests\test_ratelimit.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_ratelimit.py:8: in <module>
    from support_python import TaskRateLimiter, format_duration
E   ImportError: cannot import name 'TaskRateLimiter' from 'support_python' (C:\Dev-Projects\support.python\.plan\work\T0008-add-a-task-rate-limiter\src\support_python\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_ratelimit.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.37s ===============================
```

### Green Phase: Passing Tests and Linting

Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/test_ratelimit.py`
Exit code: `0`
```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0008-add-a-task-rate-limiter
configfile: pyproject.toml
collected 6 items

tests\test_ratelimit.py ......                                           [100%]

============================== 6 passed in 0.21s ==============================
```

Command: `C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe check .`
Exit code: `0`
```text
All checks passed!
```

Command: `C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe format --check .`
Exit code: `0`
```text
77 files already formatted
```
