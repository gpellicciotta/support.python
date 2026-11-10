## Walkthrough & Validation

### Red phase
`.venv/Scripts/python -m pytest -q tests/test_env.py`, before the implementation (exit 2):
```text
ImportError while importing test module 'C:\Dev-Projects\support.python\tests\test_env.py'.
E   ImportError: cannot import name 'user_config_dir' from 'support_python.env' (C:\Dev-Projects\support.python\src\support_python\env.py)
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

### Green phase
`.venv/Scripts/python -m pytest -q tests/test_env.py` (exit 0):
```text
11 passed, 16 subtests passed in 0.46s
```
`.venv/Scripts/python -m pytest -q` (exit 0):
```text
1102 passed, 3 skipped, 178 subtests passed in 115.20s (0:01:55)
```
`.venv/Scripts/ruff check .` (exit 0):
```text
All checks passed!
```
Python 3.9: `PYTHONPATH=src uv run --no-project --python 3.9 python -m unittest tests.test_env` (exit 0):
```text
Ran 11 tests in 0.240s

OK
```

### Integration
`test_subprocess_resolves_xdg_config_home` automates the scenario; a manual run on this Windows machine:
```text
XDG_CONFIG_HOME={{tmp}}: {{tmp}}\demo\config.json
XDG_CONFIG_HOME unset: {{home}}\AppData\Roaming\demo\config.json
```

### Review round 1 fixes
New relative-`APPDATA` and drive-qualified tool-name cases, before the fix (exit 1):
```text
SUBFAILED(name='D:foo') tests/test_env.py::UserConfigPathTests::test_invalid_tool_names_raise
SUBFAILED(environ={'APPDATA': 'relative/roaming'}) tests/test_env.py::UserConfigPathTests::test_windows_uses_appdata_with_roaming_fallback
2 failed, 11 passed, 17 subtests passed in 0.55s
```
After the fix, `.venv/Scripts/python -m pytest -q` (exit 0):
```text
1102 passed, 3 skipped, 181 subtests passed in 116.96s (0:01:56)
```
Python 3.9 rerun of `tests.test_env`:
```text
Ran 11 tests in 0.205s

OK
```
