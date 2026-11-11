# Validation Proof: T0083

## Walkthrough & Validation

### Red Phase: Failing Unit and Equivalence Tests

Command: `.venv\Scripts\python -m pytest tests\test_sql.py`
Exit code: 1

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and
configfile: pyproject.toml
plugins: timeout-2.4.0, xdist-3.8.0
timeout: 30.0s
timeout method: thread
timeout func_only: False
created: 8/8 workers
8 workers [0 items]

=================================== ERRORS ====================================
_____________________ ERROR collecting tests/test_sql.py ______________________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and\tests\test_sql.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\test_sql.py:11: in <module>
    from support_python.sql import (
E   ImportError: cannot import name 'KEEP' from 'support_python.sql' (C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and\src\support_python\sql.py)
=========================== short test summary info ===========================
ERROR tests/test_sql.py - ImportError while importing test module 'C:\Dev-Pro...
============================== 1 error in 2.88s ===============================
```

### Green Phase: Targeted Unit and Equivalence Tests

Command: `.venv\Scripts\python -m pytest tests\test_sql.py`
Exit code: 0

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and
configfile: pyproject.toml
plugins: timeout-2.4.0, xdist-3.8.0
timeout: 30.0s
timeout method: thread
timeout func_only: False
created: 8/8 workers
8 workers [20 items]

....................                                                     [100%]
============================= 20 passed in 3.72s ==============================
```

### Green Phase: Full Project Verification

Command: `python scripts/devops.py check`
Exit code: 0

```text
Command: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and\.venv\Scripts\python.exe -m ruff check .
Process ID: 73152
All checks passed!
Command: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and\.venv\Scripts\python.exe -m ruff format --check .
Process ID: 71168
165 files already formatted
Command: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and\.venv\Scripts\python.exe -m pytest -q
Process ID: 64704
[... 19 lines omitted ...]
1104 passed, 3 skipped, 168 subtests passed in 15.79s
Command: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and\.venv\Scripts\python.exe -m pytest -m slow --timeout=120
Process ID: 8324
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and
configfile: pyproject.toml
testpaths: tests
plugins: timeout-2.4.0, xdist-3.8.0
timeout: 120.0s
timeout method: thread
timeout func_only: False
created: 8/8 workers
8 workers [159 items]
........................................................................ [ 45%]
........................................................................ [ 90%]
...............                                                          [100%]
============================ 159 passed in 53.10s =============================
Command: C:\Dev-Projects\support.python\.plan\work\T0083-add-a-declarative-column-rule-transformer-builder-and\.venv\Scripts\python.exe -m build -o dist
Process ID: 20104
[... 324 lines omitted ...]
Successfully built support_python-2.0.20rc0.tar.gz and support_python-2.0.20rc0-py3-none-any.whl
```
