## Walkthrough & Validation

### Red-Phase Test Failure Proof
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/tools/test_lint_markdown.py tests/test_markdown_profiles.py -q` (exit code 1)
```text
[... 82 lines omitted ...]
=========================== short test summary info ===========================
SUBFAILED(action='check') tests/tools/test_lint_markdown.py::TestCLIAndMain::test_action_specific_help_shows_only_target_action
SUBFAILED(action='fix') tests/tools/test_lint_markdown.py::TestCLIAndMain::test_action_specific_help_shows_only_target_action
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_check_format_json_clean_directory_outputs_empty_issues_and_exits_zero
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_check_format_json_outputs_only_json_on_stdout
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_cli_config_discovery_new_name_legacy_warning_and_both_present
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_fix_dry_run_reports_planned_fixes_writes_nothing_and_exits_zero
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_fix_flag_is_unknown_option_and_exits_two
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_help_documents_actions_options_and_exit_codes
FAILED tests/test_markdown_profiles.py::test_config_filename_constants_and_load_profile_fallback
9 failed, 36 passed in 4.76s
```

### Rework Red-Phase Proof (Round 1 Findings D1 and D2)
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/tools/test_lint_markdown.py::TestCLIAndMain::test_check_format_json_error_reports_to_stderr_and_keeps_stdout_clean tests/tools/test_lint_markdown.py::TestCLIAndMain::test_cli_config_discovery_new_name_legacy_warning_and_both_present -q` (exit code 1)
```text
[... 46 lines omitted ...]
=========================== short test summary info ===========================
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_check_format_json_error_reports_to_stderr_and_keeps_stdout_clean
FAILED tests/tools/test_lint_markdown.py::TestCLIAndMain::test_cli_config_discovery_new_name_legacy_warning_and_both_present
2 failed in 1.18s
```

### Full Test Suite (Green Phase)
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest -q` (exit code 0)
```text
........................................................................ [  9%]
....................................................................s... [ 19%]
........................................................................ [ 28%]
.......s......s......................................................... [ 38%]
........................................................................ [ 48%]
........................................................................ [ 57%]
...................................................................................................................... [ 73%]
............................................................. [ 81%]
.................................................... [ 88%]
................................................ [ 95%]
.....................................                                    [100%]
745 passed, 3 skipped, 81 subtests passed in 192.28s (0:03:12)
```

### CLI Integration Verification
Command: `$env:PYTHONPATH='src'; C:\Dev-Projects\support.python\.venv\Scripts\python.exe src/support_python/tools/lint_markdown.py check --offline --format json docs; $tmp = Join-Path $env:TEMP 't0030-leg-check'; New-Item -ItemType Directory -Force -Path $tmp | Out-Null; Set-Content -Path (Join-Path $tmp 'doc.md') -Value "# Title`n`n### Skipped H3`n" -NoNewline; Set-Content -Path (Join-Path $tmp '.markdown-lint.json') -Value '{"disable": ["MD001"]}' -NoNewline; C:\Dev-Projects\support.python\.venv\Scripts\python.exe src/support_python/tools/lint_markdown.py check --offline $tmp; Remove-Item -Recurse -Force $tmp` (exit code 0)
```text
{"files_checked": 10, "issues": []}
Starting lint-markdown v2.0.15-pre+19230d3 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0030-align-lint-markdown-with-adr-0003-drop-the
**[WARN]**  Reading legacy config C:\Users\giova\AppData\Local\Temp\t0030-leg-check\.markdown-lint.json; rename it to .lint-markdown.json. The legacy filename is removed in v3.0.0.
All 1 markdown files passed linting.
Finished lint-markdown check in 0.2s with status: succeeded
```
