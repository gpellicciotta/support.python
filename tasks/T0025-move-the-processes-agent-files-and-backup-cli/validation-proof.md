## Walkthrough & Validation

### Red-Phase Proof (Import Failures After `git mv`)
Command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m pytest -q tests/tools/test_processes.py tests/tools/test_agent_files.py tests/tools/test_git_repository_backup.py`
Exit code: `2`

```text
=================================== ERRORS ====================================
_______________ ERROR collecting tests/tools/test_processes.py ________________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0025-move-the-processes-agent-files-and-backup-cli\tests\tools\test_processes.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\tools\test_processes.py:17: in <module>
    from support_python.cli_processes import build_harness, main, normalize_argv
E   ModuleNotFoundError: No module named 'support_python.cli_processes'
______________ ERROR collecting tests/tools/test_agent_files.py _______________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0025-move-the-processes-agent-files-and-backup-cli\tests\tools\test_agent_files.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\tools\test_agent_files.py:23: in <module>
    from support_python import agent_files as sync_mod
E   ImportError: cannot import name 'agent_files' from 'support_python' (C:\Dev-Projects\support.python\.plan\work\T0025-move-the-processes-agent-files-and-backup-cli\src\support_python\__init__.py)
_________ ERROR collecting tests/tools/test_git_repository_backup.py __________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0025-move-the-processes-agent-files-and-backup-cli\tests\tools\test_git_repository_backup.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\tools\test_git_repository_backup.py:22: in <module>
    from support_python import backup as backup_git_repos
E   ImportError: cannot import name 'backup' from 'support_python' (C:\Dev-Projects\support.python\.plan\work\T0025-move-the-processes-agent-files-and-backup-cli\src\support_python\__init__.py)
=========================== short test summary info ===========================
ERROR tests/tools/test_processes.py
ERROR tests/tools/test_agent_files.py
ERROR tests/tools/test_git_repository_backup.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
3 errors in 0.72s
```

### Editable Reinstall
Command: `C:/Dev-Projects/support.python/.venv/Scripts/pip.exe install --no-deps -e .`
Exit code: `0`

```text
Obtaining file:///C:/Dev-Projects/support.python/.plan/work/T0025-move-the-processes-agent-files-and-backup-cli
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
  Created wheel for support-python: filename=support_python-2.0.4rc0-0.editable-py3-none-any.whl size=12640 sha256=793f046a279283f77498ec16d3cb870ec5f0e43cab34e5285674594e210a8b37
  Stored in directory: C:\Users\giova\AppData\Local\Temp\pip-ephem-wheel-cache-zgvvlq90\wheels\ee\52\45\22c608c774b50e3fe1a50c9ba76eed45c55dbde5dc3070bec6
Successfully built support-python
Installing collected packages: support-python
  Attempting uninstall: support-python
    Found existing installation: support-python 2.0.3rc0
    Uninstalling support-python-2.0.3rc0:
      Successfully uninstalled support-python-2.0.3rc0
Successfully installed support-python-2.0.4rc0
```

### Automated Test Suite
Command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m pytest -q`
Exit code: `0`

```text
........................................................................ [ 10%]
................................................................s....... [ 20%]
........................................................................ [ 30%]
...s......s............................................................. [ 41%]
...................................................................... [ 51%]
........................................................................ [ 61%]
........................................................................ [ 71%]
............................................................ [ 80%]
.............................................................. [ 89%]
..........................................................................                               [100%]
695 passed, 3 skipped, 64 subtests passed in 171.20s (0:02:51)
```

### CLI Integration Verification
Command: `C:/Dev-Projects/support.python/.venv/Scripts/processes.exe list --format json`
Exit code: `0`

```text
[... 290 lines omitted ...]
  {
    "pid": 75624,
    "ppid": 40316,
    "name": "node.exe",
    "started": "2026-11-08T20:09:43.783839",
    "cwd": "C:\\Dev-Projects\\template.webapp"
  },
  {
    "pid": 75644,
    "ppid": 69036,
    "name": "Updates.exe",
    "started": "2026-11-09T07:42:59.139003",
    "cwd": "C:\\Users\\giova"
  }
]
Finished processes list in 0.5s with status: succeeded
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/agent-files.exe list`
Exit code: `0`

```text
Starting agent-files v2.0.4-pre+8622534 with configuration:
- Command: list
- Log file: none
- Log level: INFO
- Verbose: false
Configured AI tools
-------------------
Tool         Command  Status     Executable                                                        Version                Target                            Skills Target                       
-----------  -------  ---------  ----------------------------------------------------------------  ---------------------  --------------------------------  ------------------------------------
claude-code  claude   available  C:\Users\giova\.local\bin\claude.EXE                              2.1.306 (Claude Code)  C:\Users\giova\.claude\CLAUDE.md  C:\Users\giova\.claude\skills       
antigravity  agy      available  C:\Program Files\agy\bin\agy.EXE                                  1.3.3                  C:\Users\giova\.gemini\GEMINI.md  C:\Users\giova\.gemini\config\skills
codex-cli    codex    available  C:\Users\giova\AppData\Local\Programs\OpenAI\Codex\bin\codex.EXE  codex-cli 0.164.0      C:\Users\giova\.codex\AGENTS.md   C:\Users\giova\.agents\skills       
Finished agent-files list in 0.4s with status: succeeded
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/git-repository-backup.exe version`
Exit code: `0`

```text
backup-git-repos v2.0.4-pre+8622534 - Copyright (c) Giovanni Pellicciotta
```

### Linting & Formatting Verification
Command: `C:/Dev-Projects/support.python/.venv/Scripts/ruff.exe check .`
Exit code: `0`

```text
All checks passed!
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/ruff.exe format --check .`
Exit code: `0`

```text
94 files already formatted
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m support_python.markdown_lint check --offline docs CLAUDE.md`
Exit code: `0`

```text
Starting lint-markdown v2.0.4-pre+8622534 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0025-move-the-processes-agent-files-and-backup-cli
All 9 markdown files passed linting.
Finished lint-markdown check in 0.4s with status: succeeded
```
