## Walkthrough & Validation

Red phase, before the implementation:
```text
$ .venv/Scripts/python -m pytest -q tests/test_devops_cli.py -k description
=========================== short test summary info ===========================
FAILED tests/test_devops_cli.py::HarnessTests::test_default_description_names_deploy_after_set_deploy
FAILED tests/test_devops_cli.py::HarnessTests::test_default_description_names_enabled_service_groups
2 failed, 2 passed, 32 deselected in 0.34s
exit=1
```

Green phase, full check:
```text
$ python scripts/devops.py check
exit=0
All checks passed!
162 files already formatted
1197 passed, 3 skipped, 189 subtests passed in 124.64s (0:02:04)
Successfully built support_python-2.0.3rc0.tar.gz and support_python-2.0.3rc0-py3-none-any.whl
```

Review round 2, red phase of the collision test against fd7b2a6:
```text
$ .venv/Scripts/python -m pytest -q tests/test_devops_cli.py -k description
=========================== short test summary info ===========================
FAILED tests/test_devops_cli.py::HarnessTests::test_default_description_names_a_group_that_replaces_a_custom_action
1 failed, 5 passed, 32 deselected in 0.40s
exit=1
```

Review round 2, green phase:
```text
$ python scripts/devops.py check
exit=0
All checks passed!
1199 passed, 3 skipped, 189 subtests passed in 122.76s (0:02:02)
Successfully built support_python-2.0.3rc0.tar.gz and support_python-2.0.3rc0-py3-none-any.whl
```
