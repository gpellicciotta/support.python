### Declared Files
- pyproject.toml
- .github/workflows/python-package.yml
- docs/devops.md
- AGENTS.md
- CHANGELOG.md
- tests/{{test-module}}.py (about 10 modules gaining `@pytest.mark.slow`)

### Tests
- Unit test: none (the change adds no production code; the suites themselves are the checks)
- Integration: `pytest` runs only fast tests in parallel under 2 minutes, and `pytest -m slow --timeout=120` runs every slow test, both passing.

Completion check: `.venv/Scripts/python -m pytest` and `.venv/Scripts/python -m pytest -m slow --timeout=120`, both exiting 0.
Size estimate: 15 files, 250 lines
Size note: Most files only gain `@pytest.mark.slow` decorators; splitting by module would leave the suite half-marked.

### Notes
- The exact slow modules come from the baseline, so the declared test modules are an estimate.
- Baseline on 2026-11-10: 1163 tests in 137.6 s serial; the slowest are subprocess, git, npm, and release-pipeline integration tests.
- Out of scope: `DevopsCli` running the slow suite (T0072) and the real-state leak guard (T0073).
- Follow [testing-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/testing-guidelines.md) and [python-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/python-guidelines.md).
