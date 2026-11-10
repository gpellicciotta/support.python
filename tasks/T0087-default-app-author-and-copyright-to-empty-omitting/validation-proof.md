# Walkthrough & Validation

## Red-Phase Proof

### Default Banner Empty in cli.py
Command: `.venv\Scripts\python -m pytest tests/test_cli.py -k "test_default_banner_omits_copyright_suffix"`
Exit code: 1

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 38 items / 37 deselected / 1 selected

tests\test_cli.py F                                                      [100%]

================================== FAILURES ===================================
_______ ToolHarnessUnitTests.test_default_banner_omits_copyright_suffix _______

self = <tests.test_cli.ToolHarnessUnitTests testMethod=test_default_banner_omits_copyright_suffix>

    def test_default_banner_omits_copyright_suffix(self) -> None:
        from support_python.cli import APP_AUTHOR, COPYRIGHT, ToolHarness

>       self.assertEqual(APP_AUTHOR, "")
E       AssertionError: 'Giovanni Pellicciotta' != ''
E       - Giovanni Pellicciotta

tests\test_cli.py:362: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_default_banner_omits_copyright_suffix
====================== 1 failed, 37 deselected in 2.38s =======================
```

### DevopsCli Copyright Argument and Default Banner
Command: `.venv\Scripts\python -m pytest tests/test_devops_cli.py -k "test_version_banner or test_devops_cli_forwards_copyright"`
Exit code: 1

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 39 items / 37 deselected / 2 selected

tests\test_devops_cli.py FF                                              [100%]

================================== FAILURES ===================================
_______________ HarnessTests.test_devops_cli_forwards_copyright _______________

self = <tests.test_devops_cli.HarnessTests testMethod=test_devops_cli_forwards_copyright>

    def test_devops_cli_forwards_copyright(self) -> None:
        make_repo(self.root, venv=False)
>       cli = DevopsCli(
            PythonProject(self.root, runner=self.runner),
            copyright="Copyright (c) Custom Author",
        )
E       TypeError: DevopsCli.__init__() got an unexpected keyword argument 'copyright'

tests\test_devops_cli.py:264: TypeError
[... 13 lines omitted ...]
=========================== short test summary info ===========================
FAILED tests/test_devops_cli.py::HarnessTests::test_devops_cli_forwards_copyright
FAILED tests/test_devops_cli.py::HarnessTests::test_version_banner_shows_name_and_project_version
====================== 2 failed, 37 deselected in 2.34s =======================
```

### View Capture Empty Author Banner
Command: `.venv\Scripts\python -m pytest tests/test_capture.py -k "test_capture_app_config_default_author or test_cli_version_and_help_without_author"`
Exit code: 1

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 41 items / 39 deselected / 2 selected

tests\test_capture.py FF                                                 [100%]

================================== FAILURES ===================================
_______ CaptureCliTests.test_capture_app_config_default_author_is_empty _______

self = <tests.test_capture.CaptureCliTests testMethod=test_capture_app_config_default_author_is_empty>

    def test_capture_app_config_default_author_is_empty(self) -> None:
        cfg = CaptureAppConfig(app_name="Default App")
>       self.assertEqual(cfg.author, "")
E       AssertionError: 'Giovanni Pellicciotta' != ''
E       - Giovanni Pellicciotta

tests\test_capture.py:408: AssertionError
[... 19 lines omitted ...]
=========================== short test summary info ===========================
FAILED tests/test_capture.py::CaptureCliTests::test_capture_app_config_default_author_is_empty
FAILED tests/test_capture.py::CaptureCliTests::test_cli_version_and_help_without_author_omits_copyright
====================== 2 failed, 39 deselected in 2.38s =======================
```

### TOOLS_COPYRIGHT in support_python.tools
Command: `.venv\Scripts\python -m pytest tests/test_console_scripts.py -k "test_tools_copyright_defined_and_not_exported_from_root"`
Exit code: 1

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 17 items / 16 deselected / 1 selected

tests\test_console_scripts.py F                                          [100%]

================================== FAILURES ===================================
___________ test_tools_copyright_defined_and_not_exported_from_root ___________

    def test_tools_copyright_defined_and_not_exported_from_root() -> None:
>       from support_python.tools import TOOLS_COPYRIGHT
E       ImportError: cannot import name 'TOOLS_COPYRIGHT' from 'support_python.tools' (C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting\src\support_python\tools\__init__.py)

tests\test_console_scripts.py:85: ImportError
=========================== short test summary info ===========================
FAILED tests/test_console_scripts.py::test_tools_copyright_defined_and_not_exported_from_root
====================== 1 failed, 16 deselected in 2.09s =======================
```

## Green-Phase Proof

### Default Banner Empty in cli.py
Command: `.venv\Scripts\python -m pytest tests/test_cli.py -k "test_default_banner_omits_copyright_suffix"`
Exit code: 0

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 38 items / 37 deselected / 1 selected

tests\test_cli.py .                                                      [100%]

====================== 1 passed, 37 deselected in 1.73s =======================
```

### DevopsCli Copyright Argument and Default Banner
Command: `.venv\Scripts\python -m pytest tests/test_devops_cli.py -k "test_version_banner or test_devops_cli_forwards_copyright"`
Exit code: 0

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 39 items / 37 deselected / 2 selected

tests\test_devops_cli.py ..                                              [100%]

====================== 2 passed, 37 deselected in 1.58s =======================
```

### View Capture Empty Author Banner
Command: `.venv\Scripts\python -m pytest tests/test_capture.py -k "test_capture_app_config_default_author or test_cli_version_and_help_without_author"`
Exit code: 0

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 41 items / 39 deselected / 2 selected

tests\test_capture.py ..                                                 [100%]

====================== 2 passed, 39 deselected in 1.50s =======================
```

### TOOLS_COPYRIGHT in support_python.tools
Command: `.venv\Scripts\python -m pytest tests/test_console_scripts.py -k "test_tools_copyright_defined_and_not_exported_from_root"`
Exit code: 0

```text
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting
configfile: pyproject.toml
collected 17 items / 16 deselected / 1 selected

tests\test_console_scripts.py .                                          [100%]

====================== 1 passed, 16 deselected in 1.45s =======================
```

### Full Repository Verification: Devops Check
Command: `python scripts/devops.py check`
Exit code: 0

```text
Command: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting\.venv\Scripts\python.exe -m ruff check .
Process ID: 27176
All checks passed!
Command: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting\.venv\Scripts\python.exe -m ruff format --check .
Process ID: 20800
165 files already formatted
Command: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting\.venv\Scripts\python.exe -m pytest -q
Process ID: 71776
........................................................................ [ 71%]
......................................................... [ 76%]
....................................................... [ 80%]
................................................................... [ 86%]
.................................................................................................... [ 94%]
................................................................ [ 99%]
........                                                                 [100%]
1239 passed, 3 skipped, 206 subtests passed in 381.33s (0:06:21)
Removing dist
Command: C:\Dev-Projects\support.python\.plan\work\T0087-default-app-author-and-copyright-to-empty-omitting\.venv\Scripts\python.exe -m build -o dist
Process ID: 19936
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
  - setuptools>=77
* Getting build dependencies for sdist...
...
Successfully built support_python-2.0.16rc0.tar.gz and support_python-2.0.16rc0-py3-none-any.whl
```
