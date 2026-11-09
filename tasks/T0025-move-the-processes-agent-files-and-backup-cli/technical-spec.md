### Moves
| From                                       | To                                                |
|--------------------------------------------|---------------------------------------------------|
| `src/support_python/cli_processes.py`      | `src/support_python/tools/processes.py`           |
| `src/support_python/agent_files.py`        | `src/support_python/tools/agent_files.py`         |
| `src/support_python/agent_files_config.py` | `src/support_python/tools/agent_files_config.py`  |
| `src/support_python/backup.py`             | `src/support_python/tools/git_repository_backup.py` |
| `tests/test_processes_cli.py`              | `tests/tools/test_processes.py`                   |
| `tests/test_agent_files.py`                | `tests/tools/test_agent_files.py`                 |
| `tests/test_backup_git_repos.py`           | `tests/tools/test_git_repository_backup.py`       |
| `docs/agent-files.md`                      | `docs/tools/agent-files.md`                       |

- Add `src/support_python/tools/__init__.py` with only a module docstring.
- Add empty `tests/__init__.py` and `tests/tools/__init__.py`, so pytest and `unittest discover -s tests` can import
  `tests/tools/test_processes.py` beside `tests/test_processes.py`.
- Keep the package root re-exports (`SyncHarness`, `Tool`, `ToolRegistry`, `AgentFilesConfig`, `load_agent_files_config`, and others),
  importing from the new modules.
- Leave no compatibility shims at the old module paths; list the moves as breaking changes in `CHANGELOG.md`.
- Point console scripts at `support_python.tools.processes:main`, `support_python.tools.agent_files:main`,
  and `support_python.tools.git_repository_backup:main`.
- Fix relative imports such as `from .cli` to `from ..cli`, and absolute `support_python.agent_files` references,
  including the lazy import inside `agent_files_config`.

Mechanical command: `git mv src/support_python/cli_processes.py src/support_python/tools/processes.py`, and the same for every other row above.

### Declared Files
- pyproject.toml
- src/support_python/__init__.py
- src/support_python/tools/__init__.py
- src/support_python/tools/processes.py
- src/support_python/tools/agent_files.py
- src/support_python/tools/agent_files_config.py
- src/support_python/tools/git_repository_backup.py
- tests/__init__.py
- tests/tools/__init__.py
- tests/tools/test_processes.py
- tests/tools/test_agent_files.py
- tests/tools/test_git_repository_backup.py
- docs/tools/agent-files.md
- docs/index.md
- README.md
- CLAUDE.md
- CHANGELOG.md

### Tests
- Unit: the moved suites under `tests/tools/` pass unchanged apart from import paths and mock patch targets.
- Unit: `support_python.cli_processes`, `support_python.agent_files`, and `support_python.backup` no longer import.
- Integration: after editable reinstall, `processes list --format json`, `agent-files list`, and `git-repository-backup version` exit 0.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration commands above.
Size estimate: 17 files, 200 lines.
Size note: the moves are mechanical; most counted files carry only one-line import fix-ups, far below the line limit.
