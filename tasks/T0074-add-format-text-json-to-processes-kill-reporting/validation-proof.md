# Validation Proof: T0074

## Walkthrough & Validation

Red phase, run against the pre-change `src` (`git checkout 110e892 -- src`, restored afterward).

`python -m pytest tests/tools/test_processes.py -k format_json -q` — exit code 1

```text
E       assert 2 == 1

tests\tools\test_processes.py:209: AssertionError
=========================== short test summary info ===========================
FAILED tests/tools/test_processes.py::test_processes_kill_format_json_dry_run_reports_would_outcomes
FAILED tests/tools/test_processes.py::test_processes_kill_format_json_reports_each_pid_outcome
FAILED tests/tools/test_processes.py::test_processes_kill_format_json_failure_detail_and_inspection_error
3 failed in 2.43s
exit=1
```

Fast suite, after the change.

`python -m pytest -q` — exit code 0

```text
....uu......uu...uuu......uuuuuuuuu...................u.......u......... [ 97%]
.......................                                                  [100%]
1133 passed, 5 skipped, 181 subtests passed in 11.47s
```

Affected slow tests.

`python -m pytest -q -m slow tests/tools/test_processes.py --timeout=120` — exit code 0

```text

...                                                                      [100%]
3 passed in 4.72s
```
