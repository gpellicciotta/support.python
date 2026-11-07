## Walkthrough & Validation

### Red-Phase Test Execution (`tests/test_markdown_profiles.py`)
Ran the new profile and rule-registry test suite before implementing the `support_python.markdown` package.

- Command: `python -m pytest tests/test_markdown_profiles.py -q`
- Exit code: `2`

```text
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0016-refactor-the-ported-markdown-linter-into-registered-rule\tests\test_markdown_profiles.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\AppData\Local\Python\pythoncore-3.14-64\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_markdown_profiles.py:10: in <module>
    from support_python.markdown import (
E   ImportError: cannot import name 'ALL_RULE_CLASSES' from 'support_python.markdown' (C:\Dev-Projects\support.python\src\support_python\markdown.py)
=========================== short test summary info ===========================
ERROR tests/test_markdown_profiles.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.30s
```

### Green-Phase Markdown & Profile Test Suite
Ran the new profile/rule tests, the ported T0014 Markdown linter tests, and the table-formatting tests.

- Command: `python -m pytest tests/test_markdown_profiles.py tests/test_markdown_lint.py tests/test_markdown.py -q`
- Exit code: `0`

```text
........................................................................ [ 56%]
........................................................                 [100%]
128 passed, 2 subtests passed in 1.07s
```

### Full Repository Test Suite & Ruff Checks
Ran Ruff linting, Ruff formatting verification, and the full repository pytest suite.

- Command: `python -m ruff check src tests; python -m ruff format --check src tests; python -m pytest tests -q`
- Exit code: `0`

```text
All checks passed!
68 files already formatted
............................................................ [  7%]
.............................................................. [ 16%]
........................................................................................................ [ 29%]
........................................................................ [ 39%]
..............................s......................................... [ 49%]
....................................................................s... [ 58%]
...s.................................................................... [ 68%]
...................................................................... [ 77%]
........................................................................ [ 86%]
........................................................................ [ 96%]
...........................                                              [100%]
752 passed, 3 skipped, 64 subtests passed in 285.94s (0:04:45)
```

### Parity Verification Against `dev-guidelines` (Step 6)
Diffed `python -m support_python lint markdown check --profile dev-guidelines --offline` against `dev-guidelines/scripts/lint-markdown.py check --offline` across both `C:\Dev-Projects\dev-guidelines` and `C:\Dev-Projects\dev-guidelines\.plan\tasks`.

- Command: `$env:PYTHONPATH = "src"; python -m support_python lint markdown check --profile dev-guidelines --offline C:\Dev-Projects\dev-guidelines`
- Exit code: `0`

```text
Starting lint-markdown v1.3.2-pre+98420d2 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0016-refactor-the-ported-markdown-linter-into-registered-rule
All 54 markdown files passed linting.
Finished lint-markdown check in 0.4s with status: succeeded
```

- Command: `python -c "import subprocess, sys; ..."` (comparing issue lines on `C:\Dev-Projects\dev-guidelines` and `C:\Dev-Projects\dev-guidelines\.plan\tasks`)
- Exit code: `0`

```text
main_rc= (0, 0) main_equal= True
tasks_rc= (1, 1) tasks_count= (136, 136) tasks_equal= True
```

### Documentation Lint Verification
Verified the new documentation and changelog against the Markdown linter.

- Command: `$env:PYTHONPATH = "src"; python -m support_python lint markdown check --profile dev-guidelines --offline docs/markdown-lint.md`
- Exit code: `0`

```text
Starting lint-markdown v1.3.2-pre+98420d2 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0016-refactor-the-ported-markdown-linter-into-registered-rule
All 1 markdown files passed linting.
Finished lint-markdown check in 0.1s with status: succeeded
```
