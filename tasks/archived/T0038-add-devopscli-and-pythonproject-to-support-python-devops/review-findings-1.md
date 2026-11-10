---
task: T0038
round: 1
verdict: rejected
reviewer: "@claude-2"
reviewed_at: 2026-11-10T03:01:12Z
reviewed_commit: "ddb91cb"
base_commit: "aefdff6"
branch: task/T0038-add-devopscli-and-pythonproject-to-support-python-devops
---
# Review Findings: Task T0038 (Round 1)

## Summary
Most of the work is solid and matches the spec.
`Project`, `PythonProject`, and `DevopsCli` follow the declared API.
`scripts/devops.py` is now a thin script, and `bootstrap-dev-environment.py` still imports `_cli_common`.
Docs, README, and CHANGELOG are updated.

Re-verified by the reviewer at `ddb91cb`:
- `.venv/Scripts/python -m pytest -q`: 890 passed, 3 skipped, 86 subtests passed.
- `ruff check .` and `ruff format --check .`: clean.
- `python scripts/devops.py versions`: exit 0, versions agree.
- `python scripts/devops.py test tests/test_devops_cli.py -- -k versions`: 4 passed, 26 deselected, exit 0.
- `python scripts/devops.py help --verbose`: lists all standard actions and exit codes.
- `python scripts/devops.py release --dry-run --yes`: reaches `ReleasePipeline` and stops on the branch precondition, as expected.

Rejected for one defect: the `release` action attaches mis-versioned build outputs to every normal release.

## Defects
1. **`release` attaches pre-release-versioned artifacts to the final release** (`src/support_python/devops/cli.py`, `_release`).
   - `ReleasePipeline.run` calls `quality_check` and resolves `assets` before the freeze step (`release.py` lines 329-339).
   - `quality_check` is `project.check`, so `build` runs while `pyproject.toml` still says `X.Y.Z-pre`.
   - The wheel and sdist therefore carry `X.Y.Zrc0`.
     The task's own proof shows this: `Successfully built support_python-2.0.22rc0.tar.gz and support_python-2.0.22rc0-py3-none-any.whl`.
   - `gh release create vX.Y.Z ... dist/*rc0*` then publishes these rc0 files under tag `vX.Y.Z`.
   - `.github/workflows/publish.yml` also builds and uploads `dist/*` on `release: published`.
     The release would end up with both the rc0 files and the correct `X.Y.Z` files.
   - This contradicts the manual process in `docs/devops.md`, which builds after the freeze (step 3).
   - No test covers asset versions; `test_release_uses_check_as_quality_check_and_build_outputs_as_assets` only checks file names in a stub `dist/`.
2. **`docs/devops.md` Release Process is now inconsistent** (minor).
   - The new line says `devops.py release` "automates the steps below".
   - The steps still describe a post-freeze verification build and CI attaching packages.
     Neither matches what `release` actually does.

## Process Gaps
- The red/green evidence and integration runs are good.
  The validation proof shows the rc0 build output, but nobody checked whether those files were fit to be release assets.
- The size crossed the estimate (744 lines vs 700, 9 files vs 8); the Execution Log records this, so it's acceptable.

## Required Rework
1. Make sure `release` never publishes artifacts built from the `-pre` version. Acceptable fixes:
   - Pass no `assets` for `PythonProject` and let `publish.yml` attach the frozen-version builds.
     Keep `check` as the pre-freeze quality gate.
   - Or add a post-freeze build hook to `ReleasePipeline` and resolve assets after it.
     Record the change to `release.py` as an undeclared file.
2. Add a unit test that fails on the current behavior.
   For example: assert that release assets are not resolved from the pre-freeze build.
   Or assert that `assets` is `None` when CI publishes them.
3. Update `docs/devops.md` Release Process (and the README `release` sentence if needed) to match the chosen behavior.
4. Re-run the full suite and `python scripts/devops.py release --dry-run`, and confirm the planned `gh release create` step lists the expected assets.
