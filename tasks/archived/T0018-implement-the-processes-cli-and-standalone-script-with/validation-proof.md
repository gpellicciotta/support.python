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

### Full Repository Test Suite and Ruff Verification

Command: `.venv/Scripts/python.exe -m pytest -q && .venv/Scripts/ruff.exe check . && .venv/Scripts/ruff.exe format --check .` (Exit code: `0`)

```text
............................................................ [  8%]
.............................................................. [ 16%]
........................................................................................................ [ 30%]
........................................................................ [ 40%]
..............................s......................................... [ 50%]
.........................................s......s....................... [ 60%]
........................................................................ [ 70%]
...................................................................... [ 79%]
........................................................................ [ 89%]
........................................................................ [ 99%]
.....                                                                    [100%]
730 passed, 3 skipped, 64 subtests passed in 263.19s (0:04:23)
All checks passed!
92 files already formatted
```

### CLI Operational Verification

Command: `.venv/Scripts/python.exe scripts/processes.py list --help && .venv/Scripts/python.exe scripts/processes.py --version` (Exit code: `0`)

```text
processes v1.3.4-pre+5c21562 - Copyright (c) Giovanni Pellicciotta

Detailed Action Description: list
  Lists running processes with optional filters for cwd, open paths, start timestamps, and hierarchy trees.

Usage:
  processes list [options]

Options:
  -h, --help             show help message and exit
  --version              show version information and exit
  -v, --verbose          enable verbose output logging
  --debug                enable debug output logging
  --log-file PATH        append operational logs to specified file
  --log-level LEVEL      logging severity threshold (DEBUG, INFO, WARN, ERROR; default: INFO)
  --cwd                  Filter processes by working directory.
  --open-path            Filter processes holding an open path.
  --started-before       Upper start-time bound.
  --started-after        Lower start-time bound.
  --ancestors-of         Filter ancestors of PID.
  --descendants-of       Filter descendants of PID.
  --format               Output rendering format (table or json).

processes v1.3.4-pre+5c21562 - Copyright (c) Giovanni Pellicciotta
```
