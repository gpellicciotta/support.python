### Declared Files
- src/support_python/devops/projects.py
- src/support_python/devops/cli.py
- tests/test_devops_cli.py
- tests/test_devops_projects_gradle.py
- tests/test_devops_projects_node.py
- docs/tutorials/devops-scripts.md
- docs/devops.md
- CHANGELOG.md

### Tests
- Unit: `PythonProject` builds the slow-suite command `pytest -m slow --timeout=120` through the venv.
- Unit: `check` stops before build when the slow suite fails, and exits 1.
- Integration: Run `python scripts/devops.py test --slow` in this repository and confirm it runs only slow tests.

Completion check: `.venv/Scripts/python -m pytest tests/test_devops_cli.py tests/test_devops_projects_gradle.py tests/test_devops_projects_node.py` plus the integration scenario.
Size estimate: 8 files, 300 lines

### Notes
- Follow [testing-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/testing-guidelines.md) and [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md).
