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

## Review Round 1 Rework
Fixes [review-findings-1.md](review-findings-1.md): `release` attached assets built from the `-pre` version.

### Key Changes
- `ReleasePipeline` gained an optional `build` hook: it runs after the freeze commit and before `git tag`.
- With `build`, `assets` resolves after it; a failed build or missing asset stops before tagging or pushing.
- `DevopsCli.release` passes `build=project.build`; `check` stays the pre-freeze quality gate.
- `docs/devops.md` Release Process now has Automated Release (actual order) and Manual Release sections.
- Undeclared files: `src/support_python/devops/release.py` and `tests/test_devops_release_pipeline.py`.

### Red Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_cli.py tests/test_devops_release_pipeline.py`. Exit code: 1.
```text
E       KeyError: 'build'
E       TypeError: ReleasePipeline.__init__() got an unexpected keyword argument 'build'
FAILED tests/test_devops_cli.py::ReleaseActionTests::test_release_rebuilds_assets_after_the_freeze
FAILED tests/test_devops_release_pipeline.py::BuildHookTests::test_assets_are_built_after_the_freeze_commit_and_before_the_tag
FAILED tests/test_devops_release_pipeline.py::BuildHookTests::test_dry_run_plans_the_build_without_running_it_or_resolving_assets
FAILED tests/test_devops_release_pipeline.py::BuildHookTests::test_failed_build_stops_before_tagging_and_pushing
FAILED tests/test_devops_release_pipeline.py::BuildHookTests::test_missing_built_asset_fails_before_tagging
5 failed, 51 passed, 5 subtests passed in 27.09s
```

### Full Suite
Command: `.venv/Scripts/python -m pytest -q`. Exit code: 0. `ruff check .` and `ruff format --check .` are clean.
```text
895 passed, 3 skipped, 86 subtests passed in 118.78s (0:01:58)
```

### Integration: `release --dry-run`
In the worktree, it stops on the branch precondition, as designed (`Releases must be cut from branch 'main'`).
A throwaway clone at `cab013f` on a local `main` used the real GitHub origin, with read-only queries only.
Command: `python work/release-dry-run/scripts/devops.py release --dry-run`. Exit code: 0.
```text
Release version: v2.0.22
Next version: v2.0.23-pre
Dry run: True
[dry-run] Skipping the quality check.
[dry-run] edit CHANGELOG.md: ## v2.0.22 [released: 2026-11-10]
[dry-run] edit pyproject.toml: version = "2.0.22"
[dry-run] git add CHANGELOG.md pyproject.toml
[dry-run] git commit -m "Released version 2.0.22."
[dry-run] build release assets from the frozen version
[dry-run] git tag v2.0.22
[dry-run] git push origin main
[dry-run] git push origin v2.0.22
[dry-run] gh release create v2.0.22 --title v2.0.22 --notes-file <notes-file> <built-assets>
[dry-run] edit CHANGELOG.md: ## v2.0.23-pre
[dry-run] edit pyproject.toml: version = "2.0.23-pre"
[dry-run] git add CHANGELOG.md pyproject.toml
[dry-run] git commit -m "Started version 2.0.23-pre after the 2.0.22 release."
[dry-run] git push origin main
[dry-run] No changes were made.
Finished devops release in 4.1s with status: succeeded
```

### Post-Freeze Asset Names
The clone's version was set to `2.0.22` (simulated freeze), then built the same way as `PythonProject.build`.
`PythonProject(clone).release_assets()` then lists exactly the two frozen-version files.
```text
Successfully built support_python-2.0.22.tar.gz and support_python-2.0.22-py3-none-any.whl
['support_python-2.0.22-py3-none-any.whl', 'support_python-2.0.22.tar.gz']
```

### CI Upload Overlap
`publish.yml` uses `softprops/action-gh-release@v2` and uploads `dist/*` from the tag.
In v2.6.2, `action.yml` declares `overwrite_files`: "Overwrite existing files with the same name. Defaults to true".
Source: https://raw.githubusercontent.com/softprops/action-gh-release/v2.6.2/action.yml.
