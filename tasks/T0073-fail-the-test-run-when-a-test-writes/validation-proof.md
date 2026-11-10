# Validation Proof

## Walkthrough & Validation

### Red-Phase: Initial Failing Tests

```text
$ python -m pytest tests/test_conftest_guard.py
Exit code: 1

============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0073-fail-the-test-run-when-a-test-writes
configfile: pyproject.toml
collected 0 items / 1 error

=================================== ERRORS ====================================
________________ ERROR collecting tests/test_conftest_guard.py ________________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0073-fail-the-test-run-when-a-test-writes\tests\test_conftest_guard.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_conftest_guard.py:10: in <module>
    from tests.conftest import (
E   ModuleNotFoundError: No module named 'tests.conftest'
=========================== short test summary info ===========================
ERROR tests/test_conftest_guard.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.35s ===============================
```
