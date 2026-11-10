### API
```python
class Project:
    root: Path
    def lint(self) -> bool
    def format(self) -> bool
    def test(self, selection: Sequence[str] = ()) -> bool
    def build(self) -> bool
    def clean(self) -> bool
    def check(self) -> bool                 # lint, then test, then build; stops at the first failure
    def release_assets(self) -> list[Path]
    # version access goes through support_python.devops.release.read_version(root)

class PythonProject(Project):
    # venv at root/.venv (Scripts/python.exe on Windows, bin/python elsewhere);
    # a missing venv logs a hint to run scripts/bootstrap-dev-environment.py and fails
    # lint:   python -m ruff check .   and   python -m ruff format --check .
    # format: python -m ruff format .
    # test:   python -m pytest -q [selection]
    # build:  remove dist/, then python -m build -o dist
    # clean:  remove dist/, build/, and *.egg-info under src/
    # release_assets: dist/*.whl and dist/*.tar.gz

class DevopsCli:
    def __init__(self, project: Project, *, name: str = "devops", description: str | None = None) -> None
    def add_action(self, name: str, summary: str, handler: Callable[..., int], **kwargs) -> None   # project-specific actions
    def run(self, argv: Sequence[str] | None = None) -> int
```
- Commands run through an injectable runner defaulting to `support_python.devops.steps`, so tests can stub them.

### Command-Line Interface
```text
devops lint | format | build | check | clean
devops test [SELECTION...]
devops versions                          # version file vs CHANGELOG top heading; exit 1 on drift
devops release [--dry-run] [--skip-checks] [--yes]
devops help [--verbose] | version
```
- The banner shows `devops` and the project's version; exit codes follow ADR-0003.
- `scripts/devops.py` becomes a thin script: insert `src` into `sys.path`, then `sys.exit(DevopsCli(PythonProject(REPO_ROOT)).run())`.
- It no longer imports `_cli_common`; `bootstrap-dev-environment.py` still does.

### Declared Files
- src/support_python/devops/projects.py
- src/support_python/devops/cli.py
- src/support_python/devops/__init__.py
- tests/test_devops_cli.py
- scripts/devops.py
- docs/devops.md
- README.md
- CHANGELOG.md

### Tests
- Unit: each action runs the expected commands through the stubbed runner and maps failures to exit 1.
- Unit: `versions` exits 0 when the version file and CHANGELOG agree and 1 on drift.
- Unit: `release` passes `--dry-run`, `--skip-checks`, and `--yes` to `ReleasePipeline` (mocked).
- Unit: a missing venv exits 1 with the bootstrap hint; project-specific actions added with `add_action` dispatch.
- Integration: in this repository, `python scripts/devops.py check` and `python scripts/devops.py versions` exit 0.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration commands above.
Size estimate: 8 files, 700 lines.
Size note: the CLI, the adapter, and the dogfooded script form one contract; the script is the end-to-end check.
