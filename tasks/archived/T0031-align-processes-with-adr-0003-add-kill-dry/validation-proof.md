## Walkthrough & Validation

### Key Changes
- `processes kill --dry-run` reports `Would kill PID {{pid}}` or `Would skip protected PID {{pid}}`, terminating nothing.
- `processes list --format` accepts `text|json` (default `text`); `--format table` exits `2`.
- JSON mode routes log lines to `stderr`, so `stdout` holds one JSON document (ADR-0003).
- Added `docs/tools/processes.md`; updated `README.md`, `docs/index.md`, and `CHANGELOG.md`.

### Red Phase (before implementation)
Command: `.venv/Scripts/python -m pytest -q tests/tools/test_processes.py -k "dry_run or text_format"` (exit `1`):
```text
>       assert harness._build_parser("kill").parse_args(["123"]).dry_run is False
E       AttributeError: 'Namespace' object has no attribute 'dry_run'
>       assert text_code == 0 and expected.getvalue() in text_out
E       assert (2 == 0)
>           assert dry_res.returncode == 0 and f"Would kill PID {child.pid}" in dry_res.stdout
E           AssertionError: assert (2 == 0)
E            +  where 2 = CompletedProcess(... stderr='**[ERROR]** unrecognized arguments: --dry-run\n ...').returncode
FAILED tests/tools/test_processes.py::test_processes_kill_dry_run_reports_targets_without_terminating
FAILED tests/tools/test_processes.py::test_processes_list_text_format_matches_former_table_output
FAILED tests/tools/test_processes.py::test_processes_kill_dry_run_integration
3 failed, 5 deselected in 0.98s
```

### Green Phase
Command: `.venv/Scripts/ruff check .` / `.venv/Scripts/ruff format --check .` / `.venv/Scripts/python -m pytest -q` (exit `0`):
```text
All checks passed!
129 files already formatted
748 passed, 3 skipped, 81 subtests passed in 82.51s (0:01:22)
```

### Installed Integration Scenario
Started `python -c "import time; time.sleep(60)"`, then ran the installed `.venv/Scripts/processes` (exit codes shown):
```text
child winpid=77612
Would kill PID 77612
dry-run exit=0
alive after dry-run: True
Killed PID 77612
kill exit=0
alive after kill: False
**[ERROR]** argument --format: invalid choice: 'table' (choose from text, json)
            Usage: processes list [options]
format-table exit=2
```
Protected ancestor dry run (`processes kill <bash-pid> --dry-run`, exit `0`):
```text
**[WARN]**  Would skip protected PID 77444 (current script or ancestor process).
Finished processes kill in 0.0s with status: succeeded
```
JSON mode keeps `stdout` clean (`processes list --format json --descendants-of 99999999 2>/dev/null`, exit `0`):
```text
[]
```

### Deviation
The real kill uses `--force`, in both the automated test and the manual run.
Windows `taskkill` without `/F` cannot stop a windowless console process.
The child exits only through the tool under test; no raw OS kill calls are used.

### Markdown Lint
`lint-markdown check` on the four edited Markdown files reports 11 issues, the same as the `HEAD` baseline.
None of them are in changed lines or in `docs/tools/processes.md`.
