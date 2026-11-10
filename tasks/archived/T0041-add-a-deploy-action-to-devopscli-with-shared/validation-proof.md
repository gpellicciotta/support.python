## Walkthrough & Validation

### Key Changes
- `src/support_python/devops/deploy.py`: `DeployStep`, `DeployContext`, and `DeployPipeline` (preconditions, plan, confirmation, steps, verification).
- `src/support_python/devops/cli.py`: `DevopsCli.set_deploy` registers the `deploy` action with `--dry-run`, `--yes`, and `--skip-ci-check`.
- `src/support_python/devops/__init__.py`: re-exports the three deploy names; `tests/test_devops.py` pins them in `__all__`.
- `tests/test_devops_deploy.py`: 28 tests, all on a temporary repository with a local bare `origin` and a `gh`-only stub.

### Red Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_deploy.py` (exit 2, before the implementation).

```text
tests\test_devops_deploy.py:13: in <module>
    from support_python.devops import EXIT_COMMAND_NOT_FOUND, DeployContext, DeployStep, DevopsCli, PythonProject
E   ImportError: cannot import name 'DeployContext' from 'support_python.devops' (C:\Dev-Projects\support.python\.plan\work\T0041-add-a-deploy-action-to-devopscli-with-shared\src\support_python\devops\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_devops_deploy.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.24s
```

### Green Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_deploy.py` (exit 0).

```text
............................                                             [100%]
28 passed in 22.79s
```

The integration scenario is `DeployIntegrationTests.test_deploy_runs_command_steps_then_verification_against_a_local_bare_origin`.
It pushes an annotated `v1.0.0` tag to a bare `origin`, stubs only `gh`, and runs `run(["deploy", "--yes"])`.
Two real command steps write marker files in order, then the verification callback sees both markers.

### Full Suite and Lint
Commands: `.venv/Scripts/ruff check .`, `.venv/Scripts/ruff format --check .`, `.venv/Scripts/python -m pytest -q` (all exit 0).

```text
All checks passed!
141 files already formatted
................................................................ [ 99%]
...                                                                      [100%]
975 passed, 3 skipped, 105 subtests passed in 143.63s (0:02:23)
```

Command: `.venv/Scripts/lint-markdown check README.md CHANGELOG.md`.
The README.md and CHANGELOG.md issues it reports all predate this task; the one introduced (MD016 at the new list) was fixed.
