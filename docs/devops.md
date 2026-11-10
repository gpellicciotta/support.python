# DevOps and Operations

Practical guidance on building, testing, developing, and releasing `support-python`.

---

## Prerequisites and Environment
- **Python**: 3.9 or later (see [pyproject.toml](../pyproject.toml)'s `requires-python`).
- **Git**: Git 2.30+ supporting worktrees (`git worktree`).
- **PowerShell / Bash**: not required — [bootstrap-dev-environment.py](../scripts/bootstrap-dev-environment.py) is cross-platform.

---

## Development Workflows

### Initial Bootstrap
```bash
# Cross-platform (Windows/Linux/macOS): creates a venv, installs editable + dev extras,
# lints, tests, and builds
python scripts/bootstrap-dev-environment.py
```

### Building and Testing
```powershell
# Install in editable mode with the dev extra (pytest, ruff, build)
.venv\Scripts\pip install -e ".[dev]"

# Lint
.venv\Scripts\ruff check .
.venv\Scripts\ruff format --check .

# Run the test suite
.venv\Scripts\python -m pytest

# Build source and wheel distributions
.venv\Scripts\python -m build
```
This creates both source (`dist/*.tar.gz`) and binary wheel (`dist/*.whl`) packages.

### Scripts
Cross-platform Python scripts under `scripts/`; they are not installed with the package.

| Script                           | Purpose                                                                          |
| :------------------------------- | :------------------------------------------------------------------------------- |
| `bootstrap-dev-environment.py`   | Create the venv, install, lint, test, and build                                  |
| `devops.py`                      | Run lint, format, test, build, check, clean, versions, and release in the venv   |
| `install-from-github-release.py` | Install a released wheel from any GitHub repo (defaults to this project)         |
| `extract-release-notes.py`       | Print one version's CHANGELOG.md section for GitHub Release notes                |
| `migrate-namespace.py`           | Rename a namespace word across paths, text, version, and changelog, then release |
| `reset-history.py`               | Restart a repo from one root commit and recreate its GitHub remote (destructive) |

`_cli_common.py` is a shared helper module.
The v1.x wrapper scripts became console scripts; see [migration-v2.md](migration-v2.md).

`extract-release-notes.py`, `migrate-namespace.py`, and `reset-history.py` act on the Git repository containing the current directory.
Run them from a support-python checkout against any repository:

```bash
cd path/to/other-repo
python path/to/support.python/scripts/extract-release-notes.py 1.2.3
python path/to/support.python/scripts/migrate-namespace.py --old acme --new widgets rewrite
python path/to/support.python/scripts/reset-history.py backup ../backups
```

Each script imports `support_python` from the checkout's `src/` directory, or from an installed package.

### The devops.py Script
[devops.py](../scripts/devops.py) runs `DevopsCli(PythonProject(REPO_ROOT))` from `support_python.devops`.
It imports the package from `src/`, so it needs no install; its commands run through `.venv`.
```bash
python scripts/devops.py lint | format | build | check | clean
python scripts/devops.py test [SELECTION...] [-- PYTEST-OPTIONS...]
python scripts/devops.py versions
python scripts/devops.py release [--dry-run] [--skip-checks] [--yes]
python scripts/devops.py help [--verbose] | version
```
- `lint` runs `ruff check .` and `ruff format --check .`; `format` runs `ruff format .`.
- `test` runs `pytest -q`; `build` removes `dist/` and runs `python -m build -o dist`.
- `check` runs lint, test, and build, stopping at the first failure.
- `clean` removes `dist/`, `build/`, and `src/*.egg-info`; it needs no venv.
- `versions` compares `pyproject.toml` with the top `CHANGELOG.md` heading and exits 1 on drift.
- `release` runs `ReleasePipeline` with `check` as its quality check (see [Automated Release](#automated-release)).
- `release` rebuilds after the freeze commit and attaches the new `dist/*.whl` and `dist/*.tar.gz`.
- A missing venv exits 1 with a hint to run `bootstrap-dev-environment.py`; unknown actions exit 2.

### Task Coordination Protocol
All task work follows the `plan-task-usage-guidelines` skill from
[dev-guidelines](https://github.com/gpellicciotta/dev-guidelines). Tasks live in `PLAN.md` and
`.plan/tasks/`; change both only through `plan` commands (`plan tasks start`, `plan tasks stop`).

---

## Release Process
Ongoing work accumulates under the top `CHANGELOG.md` heading while it carries a `-pre` SemVer suffix (e.g.
`## v0.1.1-pre`), which must always match `version` in `pyproject.toml` (the single source of truth) exactly,
`-pre` included. Escalate that heading/version together the moment a change lands that needs it.

### Automated Release
`python scripts/devops.py release` releases from a clean `main`; preview it first with `--dry-run`.
It pushes and publishes, so it needs explicit approval like any tag push.
1. Check preconditions: a clean tree, `main`, an authenticated `gh`, fresh tags, no existing release, and non-empty notes.
2. Run `check` (lint, test, build) as the quality gate; `--skip-checks` skips it.
3. Ask for the typed `release vX.Y.Z` confirmation; `--yes` skips it.
4. Freeze the `CHANGELOG.md` heading and the `pyproject.toml` version, and commit.
5. Rebuild `dist/` from the frozen version; a failed build stops before anything is tagged or pushed.
6. Tag, push `main` and the tag, and publish the GitHub release with the rebuilt wheel and sdist.
7. Open the next patch `-pre` version, commit, and push.

[publish.yml](../.github/workflows/publish.yml) then builds the tag again and uploads `dist/*`.
Its same-named files replace the attached assets, since `overwrite_files` defaults to true.

### Manual Release
1. Confirm the top `CHANGELOG.md` heading's version and `pyproject.toml`'s `version` already agree.
2. Freeze: replace the heading's `-pre` suffix with `[{{date}}]`, and drop `-pre` from `pyproject.toml`'s
   `version` so both again match exactly. In the same commit, add the next patch version's `## vX.Y.Z-pre`
   heading above it (empty, ready for the next round of ongoing work) and bump `pyproject.toml`'s `version` to
   match.
3. Perform a clean verification build:
   ```powershell
   .venv\Scripts\python -m pytest && .venv\Scripts\python -m build
   ```
4. Commit the changes.
5. Once a clean build and test run succeed, commit the version freeze.
6. Tag the release commit and publish a GitHub Release.
7. CI builds distribution packages and attaches them to the GitHub Release.

### Distribution and Consumption
Downstream projects consume `support.python` via Git dependencies:
```bash
python -m pip install git+https://github.com/gpellicciotta/support.python.git@v1.0.0
```
Or declared in `pyproject.toml`:
```toml
dependencies = [
    "support-python @ git+https://github.com/gpellicciotta/support.python.git@v1.0.0",
]
```

### Tagging a Release
Once tests and builds pass:
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```
Tag pushes are an outbound action and need explicit approval.

---

## Continuous Integration
The GitHub Actions workflow in [python-package.yml](../.github/workflows/python-package.yml) triggers on push and pull requests,
executing: dependency install (with the `dev` extra), `ruff check`/`ruff format --check`, `pytest`, and
`python -m build`. [publish.yml](../.github/workflows/publish.yml) triggers on GitHub Release, building and attaching
wheel and sdist assets to the release.
