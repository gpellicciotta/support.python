## Walkthrough & Validation

### Red phase
`.venv/Scripts/python -m pytest -q tests/test_logging.py tests/test_cli.py -k "JsonOutput or subclasses_cli_logger"` (exit 1, before the implementation):
```text
FAILED tests/test_logging.py::CliLoggerJsonOutputTests::test_emit_json_honors_indent
SUBFAILED(json_output=False) tests/test_logging.py::CliLoggerJsonOutputTests::test_emit_json_writes_one_document_to_stdout
SUBFAILED(json_output=True) tests/test_logging.py::CliLoggerJsonOutputTests::test_emit_json_writes_one_document_to_stdout
FAILED tests/test_logging.py::CliLoggerJsonOutputTests::test_json_output_defaults_off
FAILED tests/test_logging.py::CliLoggerJsonOutputTests::test_json_output_redirects_console_messages_to_stderr
FAILED tests/test_cli.py::ToolHarnessJsonOutputTests::test_add_format_option_registers_standard_option
FAILED tests/test_cli.py::ToolHarnessJsonOutputTests::test_format_json_sets_json_output_and_keeps_stdout_pure
FAILED tests/test_cli.py::ToolHarnessJsonOutputTests::test_no_tool_module_subclasses_cli_logger
SUBFAILED(argv=['report']) tests/test_cli.py::ToolHarnessJsonOutputTests::test_text_format_and_actions_without_format_leave_json_output_off
SUBFAILED(argv=['report', '--format', 'text']) tests/test_cli.py::ToolHarnessJsonOutputTests::test_text_format_and_actions_without_format_leave_json_output_off
SUBFAILED(argv=['plain']) tests/test_cli.py::ToolHarnessJsonOutputTests::test_text_format_and_actions_without_format_leave_json_output_off
11 failed, 5 passed, 38 deselected in 0.48s
```

### Green phase
`.venv/Scripts/python -m pytest -q` (exit 0):
```text
1065 passed, 3 skipped, 138 subtests passed in 110.51s (0:01:50)
```

`.venv/Scripts/ruff check .` and `.venv/Scripts/ruff format --check .` (exit 0):
```text
All checks passed!
156 files already formatted
```

### Installed integration checks
Each command ran with `--verbose`; stdout went through `json.load`, stderr was searched for the banners.
```text
processes list --format json: exit=0 stdout=parses stderr Starting=1 Finished=1
agent-files list --format json: exit=0 stdout=parses stderr Starting=1 Finished=1
lint-markdown check --offline --format json docs: exit=0 stdout=parses stderr Starting=1 Finished=1
git-repository-backup list --format json --root <tmp>: exit=0 stdout=parses stderr Starting=1 Finished=1
```

`lint-markdown check --format json no-such-path`:
```text
exit=2 stdout_bytes=0
stderr:
**[ERROR]** Path does not exist: no-such-path
**[ERROR]** Finished lint-markdown check in 0.0s with status: failed
```

### JSON documents unchanged
Stdout captured with the change stashed (`before`) and applied (`after`), compared with `cmp`:
```text
af-list identical (958 bytes)
af-check identical (0 bytes)
lm-check identical (37 bytes)
lm-rules identical (2327 bytes)
grb identical (193 bytes)
proc identical (4 bytes)
```
`af-check` is empty in both runs because this repository has no `agent-digest.md`; `test_check_json_output_parses_and_reports_pending_and_up_to_date` covers its JSON.
