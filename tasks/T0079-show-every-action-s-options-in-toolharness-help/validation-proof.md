## Walkthrough & Validation

### Red phase

Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest tests/test_cli.py -q -p no:cacheprovider -n0 -k "metavars or positional or omits_action or short_option"`
Exit code: 1

```text
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_action_help_shows_metavars_and_positionals
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_verbose_help_lists_action_options_with_metavars
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_verbose_help_lists_positional_arguments
3 failed, 2 passed, 37 deselected in 0.92s
```

### Green phase

Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest -q -p no:cacheprovider`
Exit code: 0

```text
1126 passed, 5 skipped, 181 subtests passed in 11.52s
```

Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest -m slow -q -p no:cacheprovider --timeout=120 -k "help or console or cli"`
Exit code: 1

```text
SUBFAILED(arg="'version'") tests/test_cli.py::ToolHarnessSubprocessIntegrationTests::test_installed_wheel_in_foreign_repo_venv_shows_no_foreign_hash
SUBFAILED(arg="'--version'") tests/test_cli.py::ToolHarnessSubprocessIntegrationTests::test_installed_wheel_in_foreign_repo_venv_shows_no_foreign_hash
2 failed, 37 passed, 14 subtests passed in 16.31s
```

The two failures also occur on the unmodified main checkout (`-k foreign`: 2 failed, 1 passed), so T0079 did not cause them.

### help --verbose, all tools

Command: `python -m support_python.tools.{processes,agent_files,agent_digest,lint_markdown,git_repository_backup} help --verbose` and `python scripts/devops.py help --verbose`
Exit code: 0

```text
  kill
      Arguments:
        pid [pid ...]          one or more process IDs to terminate
      Options:
        -f, --force            force termination (SIGKILL or taskkill /F)
  list
      Options:
        --cwd PATH                  filter processes by working directory
        --ancestors-of PID          filter ancestors of PID
        --format {text,json}        output format (text or json; default: text)
  test (devops.py)
      Arguments:
        [selection ...]        test paths or names to run
      Options:
        --slow                 run the slow test suite
```
