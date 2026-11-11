# Validation proof

## Walkthrough & Validation

### Final checks

Command: `python -m pytest -q`
Exit code: 0

```text
bringing up nodes...
bringing up nodes...

............u.uuu....................................................... [  5%]
...............................................u..uuuu..u...u.uuu.uuuuu. [  9%]
.....uu.......uuuuuu.uu................................................. [ 14%]
uuuuuuuuuuuuu...u..uuu.........................................u.uu..... [ 18%]
............uu........................................uuu...uuu.uuuuuu.u [ 23%]
u..uu................................................uu.u....uuu.......u [ 28%]
u.u...u.uu....................................................uu........ [ 33%]
....u.u.uu....u..uu......u..u....u..u...uu...........................uu. [ 37%]
........................................................................ [ 43%]
.................................................ss..................... [ 49%]
.................................................................s...... [ 54%]
............s......................................s................uuuu [ 60%]
.........u.uu...uuuuuu..............................u..u..uuuu.........u [ 64%]
..u.uu..........u.uu.uuuu.........uuuuu...uu............................ [ 69%]
.....................................................uuu..........u.u... [ 74%]
................................................uu.uu.uuuuu.u.uu..u.u... [ 78%]
u..uu................................................................... [ 84%]
.....................uuuu.....u.u.u.u.......................u....u...... [ 89%]
........................................uu...uuu........uuuuuu.......... [ 94%]
.........................uuu................................u.........u. [ 99%]
.........                                                                [100%]
1263 passed, 5 skipped, 181 subtests passed in 18.13s
```

Command: `python -m pytest tests/test_devops_release.py tests/test_devops_versions.py tests/test_devops_release_pipeline.py tests/test_devops_cli.py -m slow --timeout=120 -q`
Exit code: 0

```text
bringing up nodes...
bringing up nodes...

...............................                                          [100%]
31 passed in 15.65s
```

Command: `python -m ruff check .`
Exit code: 0

```text
All checks passed!
```

Command: `python -m ruff format --check .`
Exit code: 0

```text
173 files already formatted
```

Command: `python -m support_python.tools.lint_markdown check CHANGELOG.md docs/tutorials/devops-scripts.md --offline`
Exit code: 0

```text
All 2 markdown files passed linting.
```

Command: `plan tasks validate C:/Dev-Projects/support.python/.plan/tasks/T0108-read-the-version-from-the-changelog-md-top.md`
Exit code: 0

```text
All 1 task file passed validation.
```

Command: `python -m build --outdir dist`
Exit code: 0

```text
[... 315 lines omitted ...]
adding 'support_python/tools/__init__.py'
adding 'support_python/tools/agent_digest.py'
adding 'support_python/tools/agent_files.py'
adding 'support_python/tools/agent_files_config.py'
adding 'support_python/tools/git_repository_backup.py'
adding 'support_python/tools/lint_markdown.py'
adding 'support_python/tools/processes.py'
adding 'support_python-3.2.0rc0.dist-info/licenses/LICENSE.md'
adding 'support_python-3.2.0rc0.dist-info/METADATA'
adding 'support_python-3.2.0rc0.dist-info/WHEEL'
adding 'support_python-3.2.0rc0.dist-info/entry_points.txt'
adding 'support_python-3.2.0rc0.dist-info/top_level.txt'
adding 'support_python-3.2.0rc0.dist-info/RECORD'
removing build\bdist.win-amd64\wheel
Successfully built support_python-3.2.0rc0.tar.gz and support_python-3.2.0rc0-py3-none-any.whl
```

All command sessions completed before handoff.


### Failing tests
Command: `python -m pytest tests/test_devops_release.py tests/test_devops_versions.py tests/test_devops_release_pipeline.py -k 'changelog_version_fallback or changelog_without_heading or missing_manifest or real_changelog_entrypoint or release_without_manifest' -m '' -n 0 -q --tb=line`
Exit code: 1

```text
FFFFFFFF                                                                 [100%]
================================== FAILURES ===================================
E   FileNotFoundError: No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_changelog_version_fallbac0
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\src\support_python\devops\release.py:74: FileNotFoundError: No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_changelog_version_fallbac0
E   FileNotFoundError: No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_changelog_version_fallbac1
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\src\support_python\devops\release.py:74: FileNotFoundError: No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_changelog_version_fallbac1
E   FileNotFoundError: No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_changelog_without_heading0
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\src\support_python\devops\release.py:74: FileNotFoundError: No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_changelog_without_heading0
E   AssertionError: assert 1 == 0
     +  where 1 = run(['versions', '2.0.0'])
     +    where run = <support_python.devops.cli.DevopsCli object at 0x000001F95F0731A0>.run
     +      where <support_python.devops.cli.DevopsCli object at 0x000001F95F0731A0> = DevopsCli(<support_python.devops.projects.GradleProject object at 0x000001F95F073500>)
---------------------------- Captured stderr call -----------------------------
**[ERROR]** No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_missing_manifest_project00
**[ERROR]** Finished devops versions in 0.0s with status: failed
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\tests\test_devops_versions.py:71: AssertionError: assert 1 == 0
E   AssertionError: assert 1 == 0
     +  where 1 = run(['versions', '2.0.0'])
     +    where run = <support_python.devops.cli.DevopsCli object at 0x000001F95F073EC0>.run
     +      where <support_python.devops.cli.DevopsCli object at 0x000001F95F073EC0> = DevopsCli(<support_python.devops.projects.PythonProject object at 0x000001F95EC07920>)
---------------------------- Captured stderr call -----------------------------
**[ERROR]** No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_missing_manifest_project10
**[ERROR]** Finished devops versions in 0.0s with status: failed
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\tests\test_devops_versions.py:71: AssertionError: assert 1 == 0
E   AssertionError: assert 1 == 0
     +  where 1 = run(['versions', '2.0.0'])
     +    where run = <support_python.devops.cli.DevopsCli object at 0x000001F95F035250>.run
     +      where <support_python.devops.cli.DevopsCli object at 0x000001F95F035250> = DevopsCli(<support_python.devops.projects.NodeProject object at 0x000001F95F0356D0>)
---------------------------- Captured stderr call -----------------------------
**[ERROR]** No version file (pyproject.toml, gradle.properties, package.json) found under C:\Users\giova\AppData\Local\Temp\pytest-of-giova\pytest-7975\test_missing_manifest_project20
**[ERROR]** Finished devops versions in 0.0s with status: failed
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\tests\test_devops_versions.py:71: AssertionError: assert 1 == 0
E   AssertionError: assert 'v1.0.0-pre' in 'devops v0.0.0+unknown\n'
     +  where 'devops v0.0.0+unknown\n' = CompletedProcess(args=['C:\\Dev-Projects\\support.python\\.venv\\Scripts\\python.exe', 'C:\\Users\\giova\\AppData\\Loc...75\\test_real_changelog_entrypoint0\\devops.py', 'version'], returncode=0, stdout='devops v0.0.0+unknown\n', stderr='').stdout
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\tests\test_devops_versions.py:107: AssertionError: assert 'v1.0.0-pre' in 'devops v0.0.0+unknown\n'
```

```text
E   assert 1 == 0
     +  where 1 = run_pipeline(dry_run=True)
     +    where run_pipeline = <tests.test_devops_release_pipeline.ChangelogOnlyTests testMethod=test_release_without_manifest>.run_pipeline
C:\Dev-Projects\support.python\.plan\work\T0108-read-the-version-from-the-changelog-md-top\tests\test_devops_release_pipeline.py:185: assert 1 == 0
=========================== short test summary info ===========================
FAILED tests/test_devops_release.py::test_changelog_version_fallback[1.2.3-pre]
FAILED tests/test_devops_release.py::test_changelog_version_fallback[1.2.3]
FAILED tests/test_devops_release.py::test_changelog_without_heading - FileNot...
FAILED tests/test_devops_versions.py::test_missing_manifest[project0] - Asser...
FAILED tests/test_devops_versions.py::test_missing_manifest[project1] - Asser...
FAILED tests/test_devops_versions.py::test_missing_manifest[project2] - Asser...
FAILED tests/test_devops_versions.py::test_real_changelog_entrypoint - Assert...
FAILED tests/test_devops_release_pipeline.py::ChangelogOnlyTests::test_release_without_manifest
8 failed, 100 deselected in 2.05s
```


