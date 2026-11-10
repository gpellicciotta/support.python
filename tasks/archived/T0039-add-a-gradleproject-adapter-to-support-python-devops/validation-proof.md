## Walkthrough & Validation

### Key Changes
- `support_python.devops.projects.GradleProject` runs the Gradle wrapper: `gradlew.bat` on Windows, `gradlew` elsewhere.
- Default task mapping follows the technical spec; `lint_tasks` through `clean_tasks` replace each list.
- Every call adds `--console=plain` through the overridable `gradle_options`.
- `test` adds `--tests ITEM` per selection item; items starting with `-` pass through unchanged.
- `release_assets` globs `build/libs/*.jar` and `*/build/libs/*.jar`.
- New `Project.release()` hook returns `None` by default; `DevopsCli` tries it before `ReleasePipeline`.
- `GradleProject.release()` confirms `release vX.Y.Z`, then runs `release_task` with `release_args`.
- `release --dry-run` runs `release_task --dry-run` without a prompt.
- `GradleProject` is exported from `support_python.devops`; README.md and CHANGELOG.md document it.

### Red Phase
Command: `python -m pytest -q tests/test_devops_projects_gradle.py` (before implementation, main checkout venv). Exit code: 2.
```text
tests\test_devops_projects_gradle.py:13: in <module>
    from support_python.devops import GradleProject
E   ImportError: cannot import name 'GradleProject' from 'support_python.devops' (C:\Dev-Projects\support.python\.plan\work\T0039-add-a-gradleproject-adapter-to-support-python-devops\src\support_python\devops\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_devops_projects_gradle.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.51s
```

### Unit Tests
Command: `python -m pytest -q tests/test_devops_projects_gradle.py tests/test_devops_cli.py tests/test_devops.py`. Exit code: 0.
```text
....................................................... [ 50%]
......................................................                   [100%]
109 passed, 17 subtests passed in 1.92s
```

### Full Suite and Lint
Command: `python -m pytest -q`. Exit code: 0.
```text
925 passed, 3 skipped, 98 subtests passed in 118.83s (0:01:58)
```
Commands: `ruff check .` and `ruff format --check .`. Exit code: 0.
```text
All checks passed!
138 files already formatted
```

### Integration: Fake Wrapper `check`
Command: `python -m pytest -q "tests/test_devops_projects_gradle.py::GradleWrapperIntegrationTests"`. Exit code: 0.
The test writes a `gradlew.bat` recording its arguments and runs `DevopsCli(GradleProject(tmp)).run(["check"])`.
It asserts exit 0 and recorded arguments `--console=plain build`.
```text
1 passed in 0.28s
```

### Integration: template.java `versions` (Read-Only)
Command: `python -c "...; sys.exit(DevopsCli(GradleProject(Path('../template.java'))).run(['versions']))"`. Exit code: 0.
```text
Starting devops v2.0.1-pre+0b429e3 with configuration:
- Command: versions
- Log file: none
- Log level: INFO
- Verbose: false
Version file: 2.0.1-pre
CHANGELOG.md: 2.0.1-pre
Versions agree.
Finished devops versions in 0.0s with status: succeeded
```
`git status --short` in template.java stayed empty afterwards.
