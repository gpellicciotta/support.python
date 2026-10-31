# DevOps and Operations

Practical guidance on building, testing, developing, and releasing `support-python`.

---

## Prerequisites and Environment

- **Python**: 3.9 or later (see `pyproject.toml`'s `requires-python`).
- **Git**: Git 2.30+ supporting worktrees (`git worktree`).
- **PowerShell / Bash**: not required — `scripts/bootstrap-dev-environment.py` is cross-platform.

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
Cross-platform Python scripts under `scripts/`; each supports `--help` and `--version`.

| Script                         | Purpose                                                                             |
| :----------------------------- | :---------------------------------------------------------------------------------- |
| `bootstrap-dev-environment.py` | Create the venv, install, lint, test, and build                                     |
| `devops.py`                    | Run `lint`, `test`, `build`, `check`, or `clean` in the venv                        |
| `kill-processes.py`            | Terminate processes by PID while protecting the script and its ancestors            |
| `backup-git-repos.py`          | Back up Git repos to bare mirrors and encrypted 7-Zip archives; restore from either |
| `reset-history.py`             | Restart a repo from one root commit and recreate its GitHub remote (destructive)    |
| `migrate-namespace.py`         | Rename a namespace word across paths, text, version, and changelog, then release    |
| `extract-release-notes.py`     | Print one version's CHANGELOG.md section for GitHub Release notes                   |

`_cli_common.py`, `_tool_common.py`, `_harness.py`, and `_repo_common.py` are shared helper modules.

### Task Coordination Protocol
All task work follows the `plan-task-usage-guidelines` skill from
[dev-guidelines](https://github.com/gpellicciotta/dev-guidelines). Tasks live in `PLAN.md` and
`.plan/tasks/`; change both only through `plan` commands (`plan tasks start`, `plan tasks stop`).

---

## Release Process

Ongoing work accumulates under the top `CHANGELOG.md` heading while it carries a `-pre` SemVer suffix (e.g.
`## v0.1.1-pre`), which must always match `version` in `pyproject.toml` (the single source of truth) exactly,
`-pre` included. Escalate that heading/version together the moment a change lands that needs it.

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

The GitHub Actions workflow in `.github/workflows/python-package.yml` triggers on push and pull requests,
executing: dependency install (with the `dev` extra), `ruff check`/`ruff format --check`, `pytest`, and
`python -m build`. `.github/workflows/publish.yml` triggers on GitHub Release, building and attaching
wheel and sdist assets to the release.
