# Validation Proof

## Walkthrough & Validation

The first parallel verification overlapped a task-log edit, triggering the real-state guard. Clean reruns passed.

### Initial fast verification
Command: `python -m pytest -n 4 --tb=short -q`

Exit code: 1

```text
.............................u...u................ [ 92%]
......uuu.uuuuuu...uu.......uuu........u...u............................ [ 97%]
...............................EE...E..E                                 [100%]
=================================== ERRORS ====================================
_____ ERROR at teardown of test_processes_help_uses_mustache_placeholders _____
[gw1] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
_ ERROR at teardown of test_processes_kill_format_json_keeps_confirmation_off_stdout _
[gw2] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
_ ERROR at teardown of SnakeCaseConfigKeyTests.test_snake_case_keys_are_accepted _
[gw3] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
_ ERROR at teardown of TestBackupJsonFormat.test_usage_error_prints_no_document _
[gw0] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
=========================== short test summary info ===========================
ERROR tests/tools/test_processes.py::test_processes_help_uses_mustache_placeholders
ERROR tests/tools/test_processes.py::test_processes_kill_format_json_keeps_confirmation_off_stdout
ERROR tests/tools/test_git_repository_backup.py::SnakeCaseConfigKeyTests::test_snake_case_keys_are_accepted
ERROR tests/tools/test_git_repository_backup.py::TestBackupJsonFormat::test_usage_error_prints_no_document
1290 passed, 5 skipped, 4 errors, 181 subtests passed in 34.09s
```

### Initial release verification
Command: `python -m pytest tests/test_devops_release_pipeline.py -m slow -n 4 --timeout=120 --tb=short -q`

Exit code: 1

```text
....E.EE.E                                  [100%]
=================================== ERRORS ====================================
_ ERROR at teardown of BuildHookTests.test_assets_are_built_after_the_freeze_commit_and_before_the_tag _
[gw1] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
_ ERROR at teardown of BuildHookTests.test_missing_built_asset_fails_before_tagging _
[gw2] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
_ ERROR at teardown of FullReleaseIntegrationTests.test_full_release_against_a_local_bare_origin _
[gw0] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
_ ERROR at teardown of BuildHookTests.test_failed_build_stops_before_tagging_and_pushing _
[gw3] win32 -- Python 3.12.8 C:\Dev-Projects\support.python\.venv\Scripts\python.exe
Real-state write guard failed! Test(s) modified protected paths:
  Modified:
    * C:\Dev-Projects\support.python\.plan\tasks\T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md
=========================== short test summary info ===========================
ERROR tests/test_devops_release_pipeline.py::BuildHookTests::test_assets_are_built_after_the_freeze_commit_and_before_the_tag
ERROR tests/test_devops_release_pipeline.py::BuildHookTests::test_missing_built_asset_fails_before_tagging
ERROR tests/test_devops_release_pipeline.py::FullReleaseIntegrationTests::test_full_release_against_a_local_bare_origin
ERROR tests/test_devops_release_pipeline.py::BuildHookTests::test_failed_build_stops_before_tagging_and_pushing
35 passed, 4 errors in 33.39s
```

### Fast suite
Command: `python -m pytest -n 4 --tb=short -q`

Exit code: 0

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  5%]
...........u.uu.u.............................uuu.uuu...uu.............. [ 10%]
...u.u..uu.u...............................................u.uuu........ [ 15%]
............................u..u..u...................uu..........uu.... [ 20%]
.........................ss.......................................uuu... [ 25%]
uuuuuuuu..uu...uuuu.uuuu..............uuuu...........................u.u [ 29%]
.uuu......................................................uu.......u.u.. [ 34%]
.u.uu......uu...u..u.....uuu....uuu......................uu....uuuuuu... [ 38%]
..uu.uuuu.uu...................uuu...................................... [ 42%]
uuu...uuu......uuu....................................................s. [ 47%]
.........s.............................................................. [ 53%]
...................s.................................................... [ 58%]
................................uu...................................... [ 64%]
..................................................uuuuu...uu...uuuu..uu. [ 68%]
........................................................................ [ 74%]
.................uuuu.............uuu................................... [ 79%]
...uuuu.......uuu.....uu.uuuu.................................uu...uuuuu [ 83%]
uuu...........................uuuu.......u.uuu.......................... [ 88%]
u..u..................uu..uuu......uu...................u.uu..uuuuuu.... [ 92%]
..............uuu...uu........................................uu........ [ 97%]
....................................                                     [100%]
1290 passed, 5 skipped, 181 subtests passed in 29.12s
```

### Release suite and CLI integration
Command: `python -m pytest tests/test_devops_release_pipeline.py -m slow -n 4 --timeout=120 --tb=short -q`

Exit code: 0

```text
bringing up nodes...
bringing up nodes...

...................................                                      [100%]
35 passed in 28.72s
```

### Ruff lint
Command: `python -m ruff check .`

Exit code: 0

```text
All checks passed!
```

### Ruff formatting
Command: `python -m ruff format --check .`

Exit code: 0

```text
174 files already formatted
```

### Package build final output
Command: `python -m build`

Exit code: 0

```text
[... 145 lines omitted ...]
adding 'support_python/logging.py'
adding 'support_python/models.py'
adding 'support_python/net.py'
adding 'support_python/processes.py'
adding 'support_python/ratelimit.py'
adding 'support_python/sql.py'
adding 'support_python/tables.py'
adding 'support_python/terminal.py'
adding 'support_python/tokens.py'
adding 'support_python/version.py'
adding 'support_python/devops/__init__.py'
adding 'support_python/devops/cli.py'
adding 'support_python/devops/deploy.py'
adding 'support_python/devops/projects.py'
adding 'support_python/devops/release.py'
adding 'support_python/devops/service_actions.py'
adding 'support_python/devops/services.py'
adding 'support_python/devops/steps.py'
adding 'support_python/markdown/__init__.py'
adding 'support_python/markdown/lint.py'
adding 'support_python/markdown/plugins.py'
adding 'support_python/markdown/profiles.py'
adding 'support_python/markdown/registry.py'
adding 'support_python/markdown/rules.py'
adding 'support_python/markdown/tables.py'
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


### Failing-first regression tests
Command: `python -m support_python.tools.lint_markdown check --offline CHANGELOG.md docs/devops.md`

Exit code: 0

```text
All 2 markdown files passed linting.
```

Command: `plan tasks validate C:/Dev-Projects/support.python/.plan/tasks/T0111-add-a-releasepipeline-hook-that-syncs-extra-version.md`

Exit code: 0

```text
All 1 task file passed validation.
```

Command: `git diff --check`

Exit code: 0

```text
```

### Initial regression output
Command: `python -m pytest tests/test_devops_release_pipeline.py -k SyncVersions -m slow -n 0 --tb=short -q`

Exit code: 1

```text
[... 11 lines omitted ...]
E   subprocess.CalledProcessError: Command '['git', 'show', 'HEAD:component.txt']' returned non-zero exit status 128.
________ SyncVersionsTests.test_dry_run_plans_sync_without_calling_it _________
tests\test_devops_release_pipeline.py:225: in test_dry_run_plans_sync_without_calling_it
    assert self.run_pipeline(sync_versions=self.sync, dry_run=True) == 0
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_devops_release_pipeline.py:160: in run_pipeline
    return self.pipeline(**overrides).run()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_devops_release_pipeline.py:156: in pipeline
    return ReleasePipeline(**options)  # type: ignore[arg-type]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: ReleasePipeline.__init__() got an unexpected keyword argument 'sync_versions'
_______ SyncVersionsTests.test_hook_failure_stops_next_commit_and_push ________
tests\test_devops_release_pipeline.py:238: in test_hook_failure_stops_next_commit_and_push
    assert self.run_pipeline(sync_versions=fail, assume_yes=True) == 1
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_devops_release_pipeline.py:160: in run_pipeline
    return self.pipeline(**overrides).run()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_devops_release_pipeline.py:156: in pipeline
    return ReleasePipeline(**options)  # type: ignore[arg-type]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: ReleasePipeline.__init__() got an unexpected keyword argument 'sync_versions'
______ SyncVersionsTests.test_sync_stages_component_in_next_commit_only _______
tests\test_devops_release_pipeline.py:217: in test_sync_stages_component_in_next_commit_only
    assert self.run_pipeline(sync_versions=self.sync, assume_yes=True) == 0
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_devops_release_pipeline.py:160: in run_pipeline
    return self.pipeline(**overrides).run()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_devops_release_pipeline.py:156: in pipeline
    return ReleasePipeline(**options)  # type: ignore[arg-type]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: ReleasePipeline.__init__() got an unexpected keyword argument 'sync_versions'
=========================== short test summary info ===========================
FAILED tests/test_devops_release_pipeline.py::SyncVersionsTests::test_cli_passes_project_hook_to_pipeline
FAILED tests/test_devops_release_pipeline.py::SyncVersionsTests::test_dry_run_plans_sync_without_calling_it
FAILED tests/test_devops_release_pipeline.py::SyncVersionsTests::test_hook_failure_stops_next_commit_and_push
FAILED tests/test_devops_release_pipeline.py::SyncVersionsTests::test_sync_stages_component_in_next_commit_only
4 failed, 1 passed, 29 deselected in 6.01s
```

