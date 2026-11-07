### Declared Files
- src/support_python/processes.py
- src/support_python/cli_processes.py
- scripts/processes.py
- tests/test_processes.py
- tests/test_processes_cli.py
- pyproject.toml
- CHANGELOG.md
- docs/index.md

Size estimate: 8 files, 400 lines

**[Estimation]** Based on existing processes module and kill-processes CLI implementation.

### Tests
- Unit: CLI parser parses `kill` and `list` subcommands and all filter flags (`--cwd`, `--open-path`, `--started-before`, `--started-after`, `--ancestors-of`, `--descendants-of`).
- Unit: Process filtering functions correctly match processes by working directory, open file paths, start timestamp boundaries, and process hierarchy relationships.
- Unit: `processes kill` refuses to terminate protected PIDs (self, parent, ancestors) and reports termination failures.
- Integration: Launch a child process with a dedicated temporary working directory and open file; verify `processes list` discovers it by `--cwd` and `--open-path`; terminate it with `processes kill` and confirm cleanup.

Completion check: python -m pytest tests/test_processes*.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Standalone script `scripts/processes.py` replaces `scripts/kill-processes.py` and provides a direct entry point.
- **[Decided]** Add a console script entry point `processes` in `pyproject.toml` pointing to `support_python.cli_processes:main`.
- **[Decided]** Keep zero third-party dependencies: implement cross-platform cwd and open-path detection in stdlib and ctypes (Win32 Restart Manager API on Windows, `/proc` on Linux, `lsof` fallback on macOS).
