## Walkthrough & Validation

### 1. Red-Phase Proof (Import Failures Before CLI Extraction)

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\python.exe" -m pytest -q tests/tools/test_lint_markdown.py
```

Exit code: `2`

```text
=================================== ERRORS ====================================
______________ ERROR collecting tests/tools/test_lint_markdown.py _____________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python\tests\tools\test_lint_markdown.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests\tools\test_lint_markdown.py:21: in <module>
    from support_python.tools import lint_markdown
E   ImportError: cannot import name 'lint_markdown' from 'support_python.tools' (C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python\src\support_python\tools\__init__.py)
=========================== short test summary info ===========================
ERROR tests/tools/test_lint_markdown.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.42s
```

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\python.exe" -m pytest -q tests/test_markdown_lint.py
```

Exit code: `1`

```text
src\support_python\markdown\lint.py:394: in check_content
    rule_issues = self._registry.run(
src\support_python\markdown\registry.py:131: in run
    issues.extend(rule.check(context))
src\support_python\markdown\rules.py:55: in check
    from support_python.markdown_lint import LintIssue
E   ModuleNotFoundError: No module named 'support_python.markdown_lint'
=========================== short test summary info ===========================
74 failed, 12 passed in 1.18s
```

### 2. Editable Reinstall

> Note: Installing `-e .` into the shared `C:\Dev-Projects\support.python\.venv` points its `.pth` entry at this worktree (`T0026-split-the-markdown-linter-into-a-support-python/src`). After merging `T0026` and removing the worktree, run `pip install --no-deps -e .` from the primary checkout on `main`.

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\pip.exe" install --no-deps -e .
```

Exit code: `0`

```text
Obtaining file:///C:/Dev-Projects/support.python/.plan/work/T0026-split-the-markdown-linter-into-a-support-python
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Building wheels for collected packages: support-python
  Building editable for support-python (pyproject.toml): started
  Building editable for support-python (pyproject.toml): finished with status 'done'
  Created wheel for support-python: filename=support_python-2.0.5-0.editable-py3-none-any.whl size=6170 sha256=d1eb9420f5d96765ab472f1e1fc1b816740fa411369d9996d54485c37717ff3c
  Stored in directory: C:\Users\giova\AppData\Local\Temp\pip-ephem-wheel-cache-d5o548y5\wheels\31\08\95\979425b7871e4643f3bf5f4b7e5f87c954e49c4b9e6c1ca44c
Successfully built support-python
Installing collected packages: support-python
  Attempting uninstall: support-python
    Found existing installation: support-python 2.0.5
    Uninstalling support-python-2.0.5:
      Successfully uninstalled support-python-2.0.5
Successfully installed support-python-2.0.5
```

### 3. Targeted and Full Test Suite

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\python.exe" -m pytest -q tests/test_markdown_lint.py tests/tools/test_lint_markdown.py tests/test_markdown_profiles.py tests/test_console_scripts.py
```

Exit code: `0`

```text
........................................................................ [ 53%]
..............................................................         [100%]
134 passed, 2 subtests passed in 11.64s
```

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\python.exe" -m pytest -q
```

Exit code: `0`

```text
........................................................................ [ 10%]
........................................................................ [ 20%]
........................................................................ [ 30%]
........................................................................ [ 41%]
........................................................................ [ 51%]
........................................................................ [ 61%]
........................................................................ [ 71%]
........................................................................ [ 81%]
........................................................................ [ 92%]
.........................................................                [100%]
698 passed, 3 skipped, 64 subtests passed in 174.78s (0:02:54)
```

### 4. Pre-Split vs. Post-Split `lint-markdown check` Comparison

Pre-split command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\lint-markdown.exe" check --offline docs README.md CHANGELOG.md
```

Exit code: `1`

```text
Starting lint-markdown v2.0.5 (943f7df) with configuration:
- Command: check
- Log level: INFO
- Log file: none
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python
CHANGELOG.md:27:1: MD014 [missing-relative-link] Relative link 'src/support_python/devops.py' does not resolve to an existing file on disk.
CHANGELOG.md:31:1: MD014 [missing-relative-link] Relative link 'src/support_python/processes.py' does not resolve to an existing file on disk.
CHANGELOG.md:32:1: MD014 [missing-relative-link] Relative link 'src/support_python/agent_files.py' does not resolve to an existing file on disk.
CHANGELOG.md:32:1: MD014 [missing-relative-link] Relative link 'src/support_python/agent_files_config.py' does not resolve to an existing file on disk.
CHANGELOG.md:33:1: MD014 [missing-relative-link] Relative link 'src/support_python/backup.py' does not resolve to an existing file on disk.
README.md:10:1: MD019 [file-references-as-links] Inline code 'pyproject.toml' references an existing project file; format it as a markdown link '[pyproject.toml](pyproject.toml)'.
README.md:211:1: MD019 [file-references-as-links] Inline code 'pyproject.toml' references an existing project file; format it as a markdown link '[pyproject.toml](pyproject.toml)'.
README.md:247:1: MD019 [file-references-as-links] Inline code 'pyproject.toml' references an existing project file; format it as a markdown link '[pyproject.toml](pyproject.toml)'.
README.md:271:1: MD019 [file-references-as-links] Inline code 'scripts/bootstrap-dev-environment.py' references an existing project file; format it as a markdown link '[bootstrap-dev-environment.py](scripts/bootstrap-dev-environment.py)'.
Finished lint-markdown check in 0.0s with status: failed
**[WARN]**  Found 9 lint issues across 10 files.
**[ERROR]** Finished lint-markdown check in 0.0s with status: failed
```

Post-split command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\lint-markdown.exe" check --offline docs README.md CHANGELOG.md
```

Exit code: `1` (identical `README.md` and `docs/` results; +1 expected `MD014` in frozen `CHANGELOG.md` `v1.3.0` line 34 for moved `src/support_python/markdown_lint.py`, matching the T0025/T0034 precedent)

```text
Starting lint-markdown v2.0.6-pre (943f7df) with configuration:
- Command: check
- Log level: INFO
- Log file: none
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python
CHANGELOG.md:27:1: MD014 [missing-relative-link] Relative link 'src/support_python/devops.py' does not resolve to an existing file on disk.
CHANGELOG.md:31:1: MD014 [missing-relative-link] Relative link 'src/support_python/processes.py' does not resolve to an existing file on disk.
CHANGELOG.md:32:1: MD014 [missing-relative-link] Relative link 'src/support_python/agent_files.py' does not resolve to an existing file on disk.
CHANGELOG.md:32:1: MD014 [missing-relative-link] Relative link 'src/support_python/agent_files_config.py' does not resolve to an existing file on disk.
CHANGELOG.md:33:1: MD014 [missing-relative-link] Relative link 'src/support_python/backup.py' does not resolve to an existing file on disk.
CHANGELOG.md:34:1: MD014 [missing-relative-link] Relative link 'src/support_python/markdown_lint.py' does not resolve to an existing file on disk.
README.md:10:1: MD019 [file-references-as-links] Inline code 'pyproject.toml' references an existing project file; format it as a markdown link '[pyproject.toml](pyproject.toml)'.
README.md:211:1: MD019 [file-references-as-links] Inline code 'pyproject.toml' references an existing project file; format it as a markdown link '[pyproject.toml](pyproject.toml)'.
README.md:247:1: MD019 [file-references-as-links] Inline code 'pyproject.toml' references an existing project file; format it as a markdown link '[pyproject.toml](pyproject.toml)'.
README.md:271:1: MD019 [file-references-as-links] Inline code 'scripts/bootstrap-dev-environment.py' references an existing project file; format it as a markdown link '[bootstrap-dev-environment.py](scripts/bootstrap-dev-environment.py)'.
Finished lint-markdown check in 0.0s with status: failed
**[WARN]**  Found 10 lint issues across 10 files.
**[ERROR]** Finished lint-markdown check in 0.0s with status: failed
```

Command (`docs/` and `CLAUDE.md`):

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\lint-markdown.exe" check --offline docs CLAUDE.md
```

Exit code: `0`

```text
Starting lint-markdown v2.0.6-pre (943f7df) with configuration:
- Command: check
- Log level: INFO
- Log file: none
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python
All 9 markdown files passed linting.
Finished lint-markdown check in 0.0s with status: succeeded
```

### 5. Ruff Lint and Format Checks

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe" check . ; & "C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe" format --check .
```

Exit code: `0`

```text
All checks passed!
96 files already formatted
```
