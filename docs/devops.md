# DevOps and Operations

How to set up, build, test, version, and release `support-python`.

---

## Development Environment
### Prerequisites
- Python 3.9 or later, matching `requires-python` in [pyproject.toml](../pyproject.toml).
- Git 2.30 or later.
- No shell: every script is a cross-platform Python script.

### Setup
Bootstrap a fresh checkout in one step:
```bash
python scripts/bootstrap-dev-environment.py
```
It creates `.venv`, installs the project in editable mode with the `dev` extra, then lints, tests, and builds.

The same steps by hand, using `.venv/Scripts/` on Windows and `.venv/bin/` elsewhere:
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/ruff check .
.venv/Scripts/ruff format --check .
.venv/Scripts/python -m pytest
.venv/Scripts/python -m build
```
The build writes a source distribution (`dist/*.tar.gz`) and a wheel (`dist/*.whl`).

---

## Versioning and Releasing
### Updating Versions
- The version lives in two places that must match exactly, `-pre` included:
  - `version` in [pyproject.toml](../pyproject.toml), without a `v` prefix.
  - The top heading of [CHANGELOG.md](../CHANGELOG.md), such as `## v2.0.51-pre`.
- Check them with `python scripts/devops.py versions`, which exits 1 when they differ.
- Set both with `python scripts/devops.py versions {{major}}.{{minor}}.{{patch}}`; add `--dry-run` to preview.
- The setter accepts an optional `-pre` suffix and always writes a development version.
- It refuses malformed versions and requires an untagged top `-pre` heading.
- The same adapter API, `Project.set_version`, supports Python, Gradle, and Node version files.
- Leave the patch number alone: `plan tasks stop` raises it in both places when a task completes.
- Bump the minor or major version by renaming both together, in the commit that needs the bump.
- At runtime, tools read the version from package metadata and append the commit hash, such as `v2.0.51-pre+c194515`.

### Making a Release
Release with [devops.py](../scripts/devops.py) from a clean `main`.
Preview first with `python scripts/devops.py release --dry-run`.
The real run pushes and publishes, so run it only with explicit approval.
1. Check preconditions: a clean tree on `main`, an authenticated `gh`, fresh tags, no existing release, and release notes.
2. Run `check` (lint, fast and slow tests, build) as the quality gate; `--skip-checks` skips it.
3. Ask for the typed `release v{{version}}` confirmation; `--yes` skips it.
4. Freeze the `CHANGELOG.md` heading and the `pyproject.toml` version, and commit.
5. Rebuild `dist/` at the frozen version; a failed build stops before anything is tagged or pushed.
6. Tag `v{{version}}`, push `main` and the tag, and publish the GitHub release with the wheel and sdist.
7. Open the next patch `-pre` version, commit, and push.

[publish.yml](../.github/workflows/publish.yml) then rebuilds the tag and replaces the release assets with its own build.

To release by hand when the pipeline cannot run:
1. Run `python scripts/devops.py versions` and `python scripts/devops.py check`.
2. Replace the `-pre` suffix of the top heading with `[released: {{yyyy-mm-dd}}]`, and drop `-pre` from `pyproject.toml`.
3. Commit the freeze, then tag it: `git tag -a v{{version}} -m "Release v{{version}}"`.
4. Push `main` and the tag, and publish a GitHub release from the tag.
5. Add the next patch `## v{{next-version}}-pre` heading, set `pyproject.toml` to match, and commit.

---

## Development Workflows
### The devops.py Script
[devops.py](../scripts/devops.py) runs `DevopsCli(PythonProject(REPO_ROOT))` from `support_python.devops`.
It imports the package from `src/`, so it needs no install; its commands run through `.venv`.
```bash
python scripts/devops.py lint | format | build | check | clean
python scripts/devops.py test [--slow] [SELECTION...] [-- PYTEST-OPTIONS...]
python scripts/devops.py versions [VERSION] [--dry-run]
python scripts/devops.py release [--dry-run] [--skip-checks] [--yes]
python scripts/devops.py help [--verbose] | version
```
- `lint` runs `ruff check .` and `ruff format --check .`; `format` runs `ruff format .`.
- `test` runs `pytest -q` (fast suite) or `pytest -m slow --timeout=120` with `--slow`.
- `build` removes `dist/` and runs `python -m build -o dist`.
- `check` runs lint, fast and slow tests, and build, stopping at the first failure.
- `clean` removes `dist/`, `build/`, and `src/*.egg-info`; it needs no venv.
- `versions` checks agreement; with `VERSION`, it updates the manifest and top development heading together.
- `release` runs `ReleasePipeline`, as described under [Making a Release](#making-a-release).
- A missing venv exits 1 with a hint to run `bootstrap-dev-environment.py`; unknown actions exit 2.

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

[_cli_common.py](../scripts/_cli_common.py) is a stdlib-only helper module shared by the scripts.
The v1.x wrapper scripts became console scripts; see [migration-v2.md](migration-v2.md).

`extract-release-notes.py`, `migrate-namespace.py`, and `reset-history.py` act on the Git repository containing the current directory.
Run them from a support-python checkout against any repository:
```bash
cd {{other-repo}}
python {{support-python}}/scripts/extract-release-notes.py 1.2.3
python {{support-python}}/scripts/migrate-namespace.py --old acme --new widgets rewrite
python {{support-python}}/scripts/reset-history.py backup ../backups
```
Each script imports `support_python` from the checkout's `src/` directory, or from an installed package.

### Task Coordination
Task work follows the `plan-task-usage-guidelines` skill shipped with [plan](https://github.com/gpellicciotta/plan).
Tasks live in `PLAN.md` and `.plan/tasks/`; change both only through `plan` commands.

---

## Distribution and Consumption
Downstream projects consume `support-python` as a Git dependency pinned to a release tag:
```bash
python -m pip install "git+https://github.com/gpellicciotta/support.python.git@v{{version}}"
```
Or declared in `pyproject.toml`:
```toml
dependencies = [
    "support-python @ git+https://github.com/gpellicciotta/support.python.git@v{{version}}",
]
```
Projects building their devops script on it pin the same tag in their `scripts/requirements.txt`.

---

## Continuous Integration
[python-package.yml](../.github/workflows/python-package.yml) runs on every push and pull request, on Python 3.9 and the latest 3.x.
The 3.9 job runs on `ubuntu-24.04`, because `setup-python` has no 3.9 build for the `ubuntu-latest` image.
It installs the `dev` extra, runs `ruff check` and `ruff format --check`, runs fast and slow tests, and builds the distributions.
[publish.yml](../.github/workflows/publish.yml) runs on a published GitHub release and attaches the wheel and sdist.
