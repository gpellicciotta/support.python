# Validation proof

## Test scenarios
- Unit: update Gradle, Python, and Node version files while preserving unrelated content and historical headings.
- Unit: reject malformed versions, finalized or missing headings, and missing manifests without modifying files.
- Unit: dry runs validate inputs and preserve both files.
- Integration: invoke a temporary devops script through Python, set its Gradle version, then check version agreement.

## Walkthrough & Validation

Red-phase command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m pytest tests/test_devops_versions.py -n 0 -x -q` (exit 1).

```text
F
================================== FAILURES ===================================
_________________________ test_set_version[project0] __________________________

project = <support_python.devops.projects.GradleProject object at 0x000001D0C37C78F0>

    def test_set_version(project):
        before = (project.root / "CHANGELOG.md").read_bytes()
>       assert project.set_version("2.0.0-pre") is True
               ^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'GradleProject' object has no attribute 'set_version'

tests\test_devops_versions.py:30: AttributeError
=========================== short test summary info ===========================
FAILED tests/test_devops_versions.py::test_set_version[project0] - AttributeE...
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 1 deselected in 1.08s
```

Command: `python scripts/devops.py check` (exit 0; tool session 91259).

```text
Command: C:\Dev-Projects\support.python\.plan\work\T0107-let-devops-versions-version-set-the-version-file\.venv\Scripts\python.exe -m ruff check .
Process ID: 42352
All checks passed!
Command: C:\Dev-Projects\support.python\.plan\work\T0107-let-devops-versions-version-set-the-version-file\.venv\Scripts\python.exe -m ruff format --check .
Process ID: 68972
173 files already formatted
Command: C:\Dev-Projects\support.python\.plan\work\T0107-let-devops-versions-version-set-the-version-file\.venv\Scripts\python.exe -m pytest -q
Process ID: 72392
[... 23 lines omitted ...]
1258 passed, 5 skipped, 181 subtests passed in 23.59s
Command: C:\Dev-Projects\support.python\.plan\work\T0107-let-devops-versions-version-set-the-version-file\.venv\Scripts\python.exe -m pytest -m slow --timeout=120
Process ID: 82344
[... 14 lines omitted ...]
============================ 166 passed in 46.16s =============================
Command: C:\Dev-Projects\support.python\.plan\work\T0107-let-devops-versions-version-set-the-version-file\.venv\Scripts\python.exe -m build -o dist
Process ID: 14664
[... 325 lines omitted ...]
adding 'support_python-3.2.0rc0.dist-info/RECORD'
removing build\bdist.win-amd64\wheel
Successfully built support_python-3.2.0rc0.tar.gz and support_python-3.2.0rc0-py3-none-any.whl
```

The first full check encountered eight guard errors after a concurrent task-log update.
The rerun above kept plan files unchanged during tests and passed without disabling guards.

Command: `.venv/Scripts/python.exe -m pytest tests/test_devops_versions.py tests/test_devops_cli.py -n 0 -q -m 'slow or not slow'` (exit 0).

```text
................................................................... [ 78%]
..................                                                       [100%]
85 passed, 5 subtests passed in 1.94s
```

Command: `.venv/Scripts/python.exe -m support_python.tools.lint_markdown check --offline CHANGELOG.md docs/devops.md docs/tutorials/devops-scripts.md` (exit 0).

```text
All 3 markdown files passed linting.
```

Command: `plan tasks validate C:/Dev-Projects/support.python/.plan/tasks/T0107-let-devops-versions-version-set-the-version-file.md` (exit 0).

```text
All 1 task file passed validation.
```

Command: `git diff --check` (exit 0).

```text

```
