# T0092 Validation Proof

## Walkthrough & Validation
```text
$ python scripts/devops.py test tests/test_devops_projects_gradle.py   -> exit 1 (before the change)
E       AssertionError: 'virtual environment' unexpectedly found in 'devops v2.0.1-pre - Copyright (c) Giovanni Pellicciotta ...
FAILED tests/test_devops_projects_gradle.py::GradleHelpTests::test_help_exit_codes_do_not_mention_a_virtual_environment
1 failed, 36 passed, 12 subtests passed in 0.83s

$ python scripts/devops.py test tests/test_devops_projects_gradle.py tests/test_devops_cli.py tests/test_devops_projects_node.py   -> exit 0
93 passed, 24 subtests passed in 4.10s

$ python scripts/devops.py check   -> exit 0
All checks passed!
162 files already formatted
1194 passed, 3 skipped, 189 subtests passed in 127.51s (0:02:07)
Successfully built support_python-2.0.2rc0.tar.gz and support_python-2.0.2rc0-py3-none-any.whl
```
