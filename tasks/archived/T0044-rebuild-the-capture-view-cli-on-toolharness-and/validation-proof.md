## Walkthrough & Validation

The worktree has no venv, so commands use the primary checkout's `.venv` with `PYTHONPATH=src`.
`support_python.__file__` resolved to the worktree's `src/support_python/__init__.py`.

### Red phase (before implementation)
Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest -q tests/test_capture.py tests/test_cli.py` (exit 2)

```text
tests\test_capture.py:28: in <module>
    from support_python.capture import DEFAULT_DELAY_SECONDS, MINIMUM_SCREENSHOT_BYTES, build_capture_harness
E   ImportError: cannot import name 'build_capture_harness' from 'support_python.capture'
ERROR tests/test_capture.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest -q tests/test_cli.py` (exit 1)

```text
SUBFAILED(name='build_action_parser') tests/test_cli.py::RemovedArgparseHelpersTests::test_removed_helpers_are_not_exposed
SUBFAILED(name='print_help') tests/test_cli.py::RemovedArgparseHelpersTests::test_removed_helpers_are_not_exposed
SUBFAILED(name='print_version') tests/test_cli.py::RemovedArgparseHelpersTests::test_removed_helpers_are_not_exposed
SUBFAILED(name='format_version') tests/test_cli.py::RemovedArgparseHelpersTests::test_removed_helpers_are_not_exposed
4 failed, 10 passed in 2.83s
```

### Green phase
Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest -q tests/test_capture.py tests/test_cli.py` (exit 0)

```text
42 passed, 11 subtests passed in 3.86s
```

Command: `ruff check . && ruff format --check . ; PYTHONPATH=src python -m pytest -q` (exit 0)

```text
All checks passed!
143 files already formatted
1036 passed, 3 skipped, 129 subtests passed in 154.27s (0:02:34)
```

Command: `grep -rn "build_action_parser\|print_help\|print_version\|build_capture_parser" README.md docs src`

```text
(no matches; scripts/ uses these names only via scripts/_cli_common.py)
```

### Integration check (spec): auth's capture-view.py
Command: `PYTHONPATH=src ../../../.venv/Scripts/python ../../../../auth/scripts/capture-view.py help` (exit 1, FAILED)

```text
  File "C:\Dev-Projects\auth\scripts\capture-view.py", line 71, in <module>
    from support_python.capture import (
ImportError: cannot import name 'build_capture_parser' from 'support_python.capture' (...). Did you mean: 'build_capture_harness'?
```

The spec assumed auth calls `run_capture_cli`. It instead imports `build_capture_parser`, `print_help`, and `print_version`.
Removing `print_help`/`print_version` breaks that import regardless of the capture rebuild.
Auth's script falls back to the sibling `support.python/src` unpinned, so it breaks once this task merges.
A backlog task in auth records the migration to `run_capture_cli`.

### Substitute check: auth's real config through run_capture_cli
`auth-migration-check.py` (this directory) execs auth's script with only the removed imports stripped, read-only.
It then calls `run_capture_cli(build_config(), argv)`.

Command: `PYTHONPATH=src python auth-migration-check.py ../../../../auth/scripts/capture-view.py help` (exit 0)

```text
capture-view v2.0.27-pre+ef0c67f - Copyright (c) Giovanni Pellicciotta

Auth View Capture
Unified visual view capture and UI screenshot automation CLI.

Usage:
  capture-view capture [TARGET] [options]
  capture-view tour [options]
  capture-view list
  capture-view version
  capture-view help [--verbose]
```

`list` and `--version` through the same shim both exited 0.

## Review Round 1 Rework

### Red phase (leading global options before an action)
Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest -q tests/test_capture.py -k leading` (exit 1)

```text
SUBFAILED(argv=['--verbose', 'list']) tests/test_capture.py::CaptureCliTests::test_cli_leading_global_option_keeps_list_action
SUBFAILED(argv=['--log-level', 'DEBUG', 'list']) tests/test_capture.py::CaptureCliTests::test_cli_leading_global_option_keeps_list_action
SUBFAILED(argv=['--port', '8000', 'list']) tests/test_capture.py::CaptureCliTests::test_cli_leading_global_option_keeps_list_action
FAILED tests/test_capture.py::CaptureCliTests::test_cli_leading_global_option_keeps_tour_action
FAILED tests/test_capture.py::CaptureCliTests::test_cli_leading_log_file_keeps_list_action
FAILED tests/test_capture.py::CaptureCliTests::test_cli_leading_option_before_version_and_help
6 failed, 2 passed, 32 deselected, 2 subtests passed in 2.05s
```

The `--mobile sign-in` and `--mode tour sign-in` cases passed before the fix, as expected.
`--port 8000 list` now dispatches to `list`, which rejects `--port` with exit 2; the test asserts that.

### Green phase
Command: `ruff check . && ruff format --check . ; PYTHONPATH=src python -m pytest -q` (exit 0)

```text
All checks passed!
143 files already formatted
1041 passed, 3 skipped, 133 subtests passed in 146.29s (0:02:26)
```

Command: `PYTHONPATH=src python auth-migration-check.py ../../../../auth/scripts/capture-view.py --verbose list | grep -c "Registered View Presets"` (exit 0)

```text
1
```

The same shim with `--verbose help` exited 0, printing `capture-view v2.0.27-pre+ef0c67f - Copyright (c) Giovanni Pellicciotta` first.
