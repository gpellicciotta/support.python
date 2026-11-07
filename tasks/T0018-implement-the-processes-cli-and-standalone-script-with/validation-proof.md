## Walkthrough & Validation

### TDD Red Phase Verification

Command: `python -m pytest tests/test_processes_cli.py` (Exit code: `2`)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
collected 0 items / 1 error

=================================== ERRORS ====================================
_______________ ERROR collecting tests/test_processes_cli.py __________________
ImportError while importing test module 'tests/test_processes_cli.py'.
tests\test_processes_cli.py:16: in <module>
    from support_python.cli_processes import build_harness, main, normalize_argv
E   ModuleNotFoundError: No module named 'support_python.cli_processes'
=========================== short test summary info ===========================
ERROR tests/test_processes_cli.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 0.14s ===============================
```

### Automated Unit, Integration, and Lint Verification

Command: `python -m pytest tests/test_processes.py tests/test_processes_cli.py && ruff check . && ruff format --check .` (Exit code: `0`)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
configfile: pyproject.toml
collected 32 items

tests\test_processes.py ............................                     [ 87%]
tests\test_processes_cli.py ....                                         [100%]

============================= 32 passed in 10.85s =============================
All checks passed!
79 files already formatted
```

### CLI Operational Verification

Command: `python scripts/processes.py --version && python scripts/processes.py list --cwd .` (Exit code: `0`)

```text
processes v1.0.18-pre+1e7e048 - Copyright (c) Giovanni Pellicciotta
Starting processes v1.0.18-pre+1e7e048 with configuration:
- Command: list
- Log file: none
- Log level: INFO
- Verbose: false
pid    ppid   name            started                     cwd
-----  -----  --------------  --------------------------  ---
44368  75252  python.exe      2026-11-07 20:12:02.001614  .
70960  73276  agy.exe         2026-11-07 20:11:16.316639  .
72036  44368  python.exe      2026-11-07 20:12:02.099615  .
75252  70960  powershell.exe  2026-11-07 20:11:48.756033  .
Finished processes list in 1.9s with status: succeeded
```
