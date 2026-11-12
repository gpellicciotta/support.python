## Walkthrough & Validation

Red phase, before the implementation:
```text
$ .venv/Scripts/python -m pytest -q tests/test_cli.py -k "fallback or leading"
            Usage: demo-tool {help|version|run} [options]
=========================== short test summary info ===========================
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_fallback_action_runs_when_the_command_line_starts_with_an_option
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_leading_options_keep_a_named_action
2 failed, 2 passed, 21 deselected in 0.38s
exit=1
```

Green phase:
```text
$ python scripts/devops.py check
All checks passed!
1202 passed, 3 skipped, 189 subtests passed in 120.23s (0:02:00)
Successfully built support_python-2.0.4rc0.tar.gz and support_python-2.0.4rc0-py3-none-any.whl
exit=0
```

Review round 2, red phase of the new tests against 4c96102:
```text
$ .venv/Scripts/python -m pytest -q tests/test_cli.py -k "arity or help_target"
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_leading_global_values_keep_the_help_target
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_leading_options_use_each_actions_arity_and_skip_action_names
2 failed, 25 deselected in 0.38s
exit=1
```

Review round 2, green phase:
```text
$ python scripts/devops.py check
All checks passed!
1204 passed, 3 skipped, 189 subtests passed in 130.16s (0:02:10)
Successfully built support_python-2.0.4rc0.tar.gz and support_python-2.0.4rc0-py3-none-any.whl
exit=0
```

Review round 3, red phase of the abbreviation and bundling cases against 852b683:
```text
$ .venv/Scripts/python -m pytest -q tests/test_cli.py -k arity
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_leading_options_use_each_actions_arity_and_skip_action_names
1 failed, 26 deselected in 0.37s
exit=1
```

Review round 3, green phase:
```text
$ python scripts/devops.py check
All checks passed!
1204 passed, 3 skipped, 189 subtests passed in 118.87s (0:01:58)
Successfully built support_python-2.0.4rc0.tar.gz and support_python-2.0.4rc0-py3-none-any.whl
exit=0
```
