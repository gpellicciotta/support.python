# T0001 Validation Proof

## Walkthrough & Validation
Command: `python -m pytest tests/test_files.py` (exit code 1, red phase before implementation)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0001-add-atomic-text-write-helpers-with-windows-safe
configfile: pyproject.toml
collected 0 items / 1 error

=================================== ERRORS ====================================
____________________ ERROR collecting tests/test_files.py _____________________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0001-add-atomic-text-write-helpers-with-windows-safe\tests\test_files.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_files.py:14: in <module>
    from support_python import (
E   ImportError: cannot import name 'atomic_replace' from 'support_python' (C:\Dev-Projects\support.python\.plan\work\T0001-add-atomic-text-write-helpers-with-windows-safe\src\support_python\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_files.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.83s ===============================
```

Command: `python -m pytest tests/test_files.py` (exit code 0, green phase after implementation)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0001-add-atomic-text-write-helpers-with-windows-safe
configfile: pyproject.toml
collected 9 items

tests\test_files.py ..s......                                            [100%]

======================== 8 passed, 1 skipped in 1.01s =========================
```

Command: `python -m pytest tests/test_files.py tests/test_version.py tests/test_cli.py` (exit code 0)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0001-add-atomic-text-write-helpers-with-windows-safe
configfile: pyproject.toml
collected 30 items

tests\test_files.py ..s......                                            [ 30%]
tests\test_version.py ........                                           [ 56%]
tests\test_cli.py .............                                          [100%]

======================== 29 passed, 1 skipped in 0.83s ========================
```

Command: `ruff check .` (exit code 0)

```text
All checks passed!
```

Command: `ruff format --check .` (exit code 0)

```text
71 files already formatted
```
