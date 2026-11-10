## Walkthrough & Validation

### Key Changes
- `support_python.devops.projects`: abstract `Project` (with `check` and `release_assets`) and `PythonProject` over `.venv`.
- `support_python.devops.cli`: `DevopsCli` on `ToolHarness` with lint, format, test, build, check, clean, versions, and release.
- `release` builds `ReleasePipeline` with `check` as quality check, `release_assets` as assets, and the project runner.
- `scripts/devops.py` inserts `src` into `sys.path` and runs `DevopsCli(PythonProject(REPO_ROOT))`; it no longer imports `_cli_common`.
- `test` takes paths as `SELECTION`; pytest options go after `--`.

### Red Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_cli.py` (before implementation). Exit code: 2.
```text
=================================== ERRORS ====================================
__________________ ERROR collecting tests/test_devops_cli.py __________________
...
tests\test_devops_cli.py:12: in <module>
    from support_python.devops.cli import DevopsCli
E   ModuleNotFoundError: No module named 'support_python.devops.cli'
=========================== short test summary info ===========================
ERROR tests/test_devops_cli.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.36s
```

### Unit Tests
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_cli.py tests/test_devops.py`. Exit code: 0.
```text
................................................................... [ 85%]
...........                                                              [100%]
78 passed, 5 subtests passed in 1.29s
```

### Integration: `python scripts/devops.py check`
Exit code: 0. Runs ruff, the full pytest suite, and build through the worktree `.venv` (paths shortened).
```text
Starting devops v2.0.22-pre+aefdff6 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
Command: .venv\Scripts\python.exe -m ruff check .
Process ID: 58284
All checks passed!
Command: .venv\Scripts\python.exe -m ruff format --check .
Process ID: 72820
137 files already formatted
Command: .venv\Scripts\python.exe -m pytest -q
Process ID: 70476
...
890 passed, 3 skipped, 86 subtests passed in 112.72s (0:01:52)
...
Successfully built support_python-2.0.22rc0.tar.gz and support_python-2.0.22rc0-py3-none-any.whl
Finished devops check in 119.8s with status: succeeded
```

### Integration: `python scripts/devops.py versions`
Exit code: 0.
```text
Starting devops v2.0.22-pre+aefdff6 with configuration:
- Command: versions
- Log file: none
- Log level: INFO
- Verbose: false
Version file: 2.0.22-pre
CHANGELOG.md: 2.0.22-pre
Versions agree.
Finished devops versions in 0.0s with status: succeeded
```

### Additional Spot Checks
- `python scripts/devops.py test tests/test_devops_cli.py -- -k versions`: exit 0, `4 passed, 26 deselected`.
- `python scripts/devops.py release --dry-run`: reached `ReleasePipeline` (`Release version: v2.0.22`, `Next version: v2.0.23-pre`, `Dry run: True`).
  It then exited 1 on the uncommitted-changes precondition, as designed; nothing was changed.
- `python scripts/devops.py clean`: exit 0, removed `dist` and `src/support_python.egg-info`; the editable install still imports.
- `ruff check .` and `ruff format --check .`: clean.
- `lint-markdown check README.md docs/devops.md CHANGELOG.md`: no new issues versus `main`.
  The only extra finding is `PLAN.md` not existing in the worktree.
