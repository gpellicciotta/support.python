## Walkthrough & Validation

### 1. Red-Phase Proof (Import Failures Before CLI Extraction)

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\python.exe" -m pytest -q tests/test_markdown_lint.py tests/tools/test_lint_markdown.py
```

Exit code: `2`

```text
=================================== ERRORS ====================================
_____________ ERROR collecting tests/tools/test_lint_markdown.py ______________
ImportError while importing test module 'C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python\tests\tools\test_lint_markdown.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
C:\Program Files\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\tools\test_lint_markdown.py:21: in <module>
    from support_python.tools import lint_markdown
E   ImportError: cannot import name 'lint_markdown' from 'support_python.tools' (C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python\src\support_python\tools\__init__.py)
=========================== short test summary info ===========================
ERROR tests/tools/test_lint_markdown.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.12s
```

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\python.exe" -m pytest -q tests/test_markdown_lint.py
```

Exit code: `1` (tail of `task-69.log`)

```text
src\support_python\markdown\lint.py:731: in lint_content
    issues.extend(rule.check(ctx))
                  ^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <support_python.markdown.rules.MD019FileReferencesAsLinks object at 0x000001AFCBE60B60>
ctx = LintContext(file_path=WindowsPath('C:/Users/giova/AppData/Local/Temp/tmp0_8_17qs/CHANGELOG.md'), actual_file_path=Wind...fence_lang='', heading_level=1, heading_title='Versioned Changes', prev_heading_level=0, h1_count=1, bullet_match=None)

    def check(self, ctx: LintContext) -> list[LintIssue]:
>       from support_python.markdown_lint import MarkdownLinter
E       ModuleNotFoundError: No module named 'support_python.markdown_lint'

src\support_python\markdown\rules.py:378: ModuleNotFoundError
=========================== short test summary info ===========================
FAILED tests/test_markdown_lint.py::TestRuleMD019FileReferencesAsLinks::test_proper_markdown_link_passes
FAILED tests/test_markdown_lint.py::TestMarkdownLinterFix::test_fix_content_table_alignment_idempotence_three_passes
FAILED tests/test_markdown_lint.py::TestEngineModuleIsolation::test_engine_module_does_not_load_argparse_or_cli
FAILED tests/test_markdown_lint.py::TestDiscoverMarkdownFilesGitIgnore::test_root_relative_link_resolves_against_project_root
FAILED tests/test_markdown_lint.py::TestChangelogReleasedHeadings::test_released_date_tag_after_cutoff_flags_md014_and_md019
FAILED tests/test_markdown_lint.py::TestChangelogReleasedHeadings::test_released_date_tag_before_cutoff_exempts_md014_and_md019
FAILED tests/test_markdown_lint.py::TestChangelogReleasedHeadings::test_released_date_tag_case_insensitive
74 failed, 12 passed in 9.75s
```

### 2. Editable Reinstall (`task-211`)

> Note: Installing `-e .` into the shared `C:\Dev-Projects\support.python\.venv` points its editable `.pth` entry at this worktree (`T0026-split-the-markdown-linter-into-a-support-python/src`). After merging `T0026` and removing the worktree, run `pip install --no-deps -e .` from the primary checkout on `main`.

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
  Created wheel for support-python: filename=support_python-2.0.6rc0-0.editable-py3-none-any.whl size=12659 sha256=de0e366daf457b5f2110bb974b2df06f894e1509f746fb672fca776ff1e0c8e5
  Stored in directory: C:\Users\giova\AppData\Local\Temp\pip-ephem-wheel-cache-xk2f_5h0\wheels\c6\fb\f1\7a33e08fd348e05229a42a899c5439d1a7833a8e8fa6f6d02c
Successfully built support-python
Installing collected packages: support-python
  Attempting uninstall: support-python
    Found existing installation: support-python 2.0.6rc0
    Uninstalling support-python-2.0.6rc0:
      Successfully uninstalled support-python-2.0.6rc0
Successfully installed support-python-2.0.6rc0

[notice] A new release of pip is available: 26.2.2 -> 26.3
[notice] To update, run: python.exe -m pip install --upgrade pip
```

### 3. Targeted and Full Test Suite (`task-137` and `task-116`)

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

Both commands were executed from the worktree (`C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python`). Both exit with code `1` and report the exact same `10 lint issues across 10 files` (only the version banner differs: `v2.0.5-pre+8450b1e` on `main` vs. `v2.0.6-pre+e100006` on the task branch).

Pre-split command (`main`'s `support_python.markdown_lint.main` loaded from `C:\Dev-Projects\support.python\src` with `python.exe -I`):

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\python.exe" -I -c "import sys; sys.path.insert(0, r'C:\Dev-Projects\support.python\src'); from support_python.markdown_lint import main; raise SystemExit(main(['check', '--offline', 'docs', 'README.md', 'CHANGELOG.md']))"
```

Exit code: `1`

```text
Starting lint-markdown v2.0.5-pre+8450b1e with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python
CHANGELOG.md:32:115: MD014 [valid-relative-links] Relative link 'src/support_python/agent_files_config.py' does not resolve to an existing file on disk
CHANGELOG.md:32:178: MD014 [valid-relative-links] Relative link 'docs/agent-files.md' does not resolve to an existing file on disk
CHANGELOG.md:33:59: MD014 [valid-relative-links] Relative link 'src/support_python/agent_files.py' does not resolve to an existing file on disk
CHANGELOG.md:34:54: MD014 [valid-relative-links] Relative link 'src/support_python/markdown_lint.py' does not resolve to an existing file on disk
CHANGELOG.md:35:188: MD014 [valid-relative-links] Relative link 'src/support_python/backup.py' does not resolve to an existing file on disk
CHANGELOG.md:36:123: MD014 [valid-relative-links] Relative link 'src/support_python/devops.py' does not resolve to an existing file on disk
README.md:10:10: MD014 [valid-relative-links] Relative link 'PLAN.md' does not resolve to an existing file on disk
README.md:31:1: MD019 [file-references-as-links] Repository file reference '.github/workflows/python-package.yml' in prose must be formatted as markdown link [filename](path)
README.md:113:1: MD016 [no-blank-line-before-list] Sentence introducing a list must not be followed by a blank line
README.md:355:40: MD019 [file-references-as-links] Repository file reference '.github/workflows/publish.yml' in prose must be formatted as markdown link [filename](path)
**[WARN]**  Found 10 lint issues across 10 files.
**[ERROR]** Finished lint-markdown check in 0.4s with status: failed
```

Post-split command (installed `lint-markdown.exe`):

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\lint-markdown.exe" check --offline docs README.md CHANGELOG.md
```

Exit code: `1`

```text
Starting lint-markdown v2.0.6-pre+e100006 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python
CHANGELOG.md:32:115: MD014 [valid-relative-links] Relative link 'src/support_python/agent_files_config.py' does not resolve to an existing file on disk
CHANGELOG.md:32:178: MD014 [valid-relative-links] Relative link 'docs/agent-files.md' does not resolve to an existing file on disk
CHANGELOG.md:33:59: MD014 [valid-relative-links] Relative link 'src/support_python/agent_files.py' does not resolve to an existing file on disk
CHANGELOG.md:34:54: MD014 [valid-relative-links] Relative link 'src/support_python/markdown_lint.py' does not resolve to an existing file on disk
CHANGELOG.md:35:188: MD014 [valid-relative-links] Relative link 'src/support_python/backup.py' does not resolve to an existing file on disk
CHANGELOG.md:36:123: MD014 [valid-relative-links] Relative link 'src/support_python/devops.py' does not resolve to an existing file on disk
README.md:10:10: MD014 [valid-relative-links] Relative link 'PLAN.md' does not resolve to an existing file on disk
README.md:31:1: MD019 [file-references-as-links] Repository file reference '.github/workflows/python-package.yml' in prose must be formatted as markdown link [filename](path)
README.md:113:1: MD016 [no-blank-line-before-list] Sentence introducing a list must not be followed by a blank line
README.md:355:40: MD019 [file-references-as-links] Repository file reference '.github/workflows/publish.yml' in prose must be formatted as markdown link [filename](path)
**[WARN]**  Found 10 lint issues across 10 files.
**[ERROR]** Finished lint-markdown check in 0.4s with status: failed
```

Command (`docs/` and `CLAUDE.md`):

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\lint-markdown.exe" check --offline docs CLAUDE.md
```

Exit code: `0`

```text
Starting lint-markdown v2.0.6-pre+e100006 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python\.plan\work\T0026-split-the-markdown-linter-into-a-support-python
All 9 markdown files passed linting.
Finished lint-markdown check in 0.4s with status: succeeded
```

### 5. Ruff Lint and Format Checks

Command:

```powershell
& "C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe" check . ; if ($LASTEXITCODE -eq 0) { & "C:\Dev-Projects\support.python\.venv\Scripts\ruff.exe" format --check . }
```

Exit code: `0`

```text
All checks passed!
96 files already formatted
```
