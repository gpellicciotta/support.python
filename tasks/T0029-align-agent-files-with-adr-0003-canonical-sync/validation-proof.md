## Walkthrough & Validation

### Red-Phase Test Run (Before Implementation)
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/tools/test_agent_files.py -q`
Exit code: `1`
```text
[... 184 lines omitted ...]
FAILED tests/tools/test_agent_files.py::MainCliLoggingTests::test_check_writes_start_and_end_banner_to_log_file
SUBFAILED(action='sync') tests/tools/test_agent_files.py::HarnessHelpTests::test_action_specific_help_shows_only_target_action
SUBFAILED(action='check') tests/tools/test_agent_files.py::HarnessHelpTests::test_action_specific_help_shows_only_target_action
FAILED tests/tools/test_agent_files.py::HarnessHelpTests::test_bare_invocation_shows_full_help_and_exits_zero
FAILED tests/tools/test_agent_files.py::HarnessHelpTests::test_help_subcommand_with_action_argument
SUBFAILED(argv=['help']) tests/tools/test_agent_files.py::HarnessHelpTests::test_non_verbose_help_documents_actions_and_options
SUBFAILED(argv=['--help']) tests/tools/test_agent_files.py::HarnessHelpTests::test_non_verbose_help_documents_actions_and_options
SUBFAILED(argv=['-h']) tests/tools/test_agent_files.py::HarnessHelpTests::test_non_verbose_help_documents_actions_and_options
FAILED tests/tools/test_agent_files.py::HarnessHelpTests::test_verbose_help_adds_action_details_and_examples
FAILED tests/tools/test_agent_files.py::HarnessErrorFormattingTests::test_invalid_option_logs_indicator_error_and_exits_two
FAILED tests/tools/test_agent_files.py::HarnessErrorFormattingTests::test_unknown_tool_name_logs_indicator_error_and_exits_two
SUBFAILED(verb='update') tests/tools/test_agent_files.py::HarnessErrorFormattingTests::test_update_and_diff_are_rejected_as_unknown_actions_exiting_two
SUBFAILED(verb='diff') tests/tools/test_agent_files.py::HarnessErrorFormattingTests::test_update_and_diff_are_rejected_as_unknown_actions_exiting_two
FAILED tests/tools/test_agent_files.py::SupportPythonAgentFilesCliTests::test_check_json_output_parses_and_reports_pending_and_up_to_date
FAILED tests/tools/test_agent_files.py::SupportPythonAgentFilesCliTests::test_list_json_output_parses_and_contains_documented_keys
FAILED tests/tools/test_agent_files.py::AgentFilesConfigTests::test_config_discovery_prefers_dotfile_and_warns_on_legacy
FAILED tests/tools/test_agent_files.py::AgentFilesConfigTests::test_load_config_defaults_when_no_file_present
17 failed, 87 passed, 7 subtests passed in 4.84s
```

### Green-Phase Test Suite
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest -q`
Exit code: `0`
```text
........................................................................ [ 10%]
...................................................................s.... [ 20%]
........................................................................ [ 30%]
......s......s.......................................................... [ 40%]
........................................................................ [ 50%]
........................................................................ [ 60%]
.................................................................................................................................. [ 78%]
........................................................ [ 86%]
...............................................................................................              [100%]
710 passed, 3 skipped, 66 subtests passed in 181.05s (0:03:01)
```

### Focused Agent-Files Test Suite (Including Installed CLI Integration)
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/tools/test_agent_files.py -q`
Exit code: `0`
```text
.......................................................... [ 59%]
........................................                                 [100%]
98 passed, 14 subtests passed in 5.49s
```

### Installed CLI End-to-End Verification
Command: `C:\Dev-Projects\support.python\.venv\Scripts\agent-files.exe list --format json`
Exit code: `0`
```text
[
  {
    "tool": "claude-code",
    "command": "claude",
    "status": "available",
    "available": true,
    "executable": "C:\\Users\\giova\\.local\\bin\\claude.EXE",
    "version": "2.1.306 (Claude Code)",
    "instructions_file": "C:\\Users\\giova\\.claude\\CLAUDE.md",
    "target": "C:\\Users\\giova\\.claude\\CLAUDE.md",
    "skills_dir": "C:\\Users\\giova\\.claude\\skills",
    "skills_target": "C:\\Users\\giova\\.claude\\skills"
  },
[... 24 lines omitted ...]
  }
]
```

### Linting and Formatting Checks
Command: `C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe check src/support_python/tools/agent_files.py src/support_python/tools/agent_files_config.py tests/tools/test_agent_files.py`
Exit code: `0`
```text
All checks passed!
```

Command: `C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe format --check src/support_python/tools/agent_files.py src/support_python/tools/agent_files_config.py tests/tools/test_agent_files.py`
Exit code: `0`
```text
3 files already formatted
```

Command: `C:\Dev-Projects\support.python\.venv\Scripts\lint-markdown.exe check --offline docs/tools/agent-files.md`
Exit code: `0`
```text
Starting lint-markdown v2.0.10-pre+f0e01fb with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0029-align-agent-files-with-adr-0003-canonical-sync
All 1 markdown files passed linting.
Finished lint-markdown check in 0.1s with status: succeeded
```
