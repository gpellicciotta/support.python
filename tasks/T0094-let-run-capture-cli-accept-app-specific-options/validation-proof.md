## Walkthrough & Validation

Red phase, before the implementation:
```text
$ .venv/Scripts/python -m pytest -q tests/test_capture.py -k app_options
SUBFAILED(argv=['capture', 'account', '--theme', 'dark']) tests/test_capture.py::CaptureCliTests::test_cli_app_options_reach_the_capture_handler
SUBFAILED(argv=['--theme', 'light', 'account']) tests/test_capture.py::CaptureCliTests::test_cli_app_options_reach_the_capture_handler
FAILED tests/test_capture.py::CaptureCliTests::test_cli_app_options_reach_the_capture_handler
3 failed, 1 passed, 37 deselected in 0.38s
exit=1
```

Green phase:
```text
$ python scripts/devops.py check
All checks passed!
1206 passed, 3 skipped, 191 subtests passed in 117.28s (0:01:57)
Successfully built support_python-2.0.5rc0.tar.gz and support_python-2.0.5rc0-py3-none-any.whl
exit=0
```
