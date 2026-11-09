### Console Scripts
```toml
[project.scripts]
processes = "support_python.cli_processes:main"
agent-files = "support_python.agent_files:main"
lint-markdown = "support_python.markdown_lint:main"
git-repository-backup = "support_python.backup:main"
```
- Remove `support-python = "support_python.cli:main"`.
- Keep the current module paths; T0025 moves the modules into `support_python.tools`.
- `git-repository-backup` keeps the `backup-git-repos` banner and config path until T0027 renames them.
- agent-files keeps `update`/`diff` and its `sync`/`check` aliases until T0029.

### Removals
- Delete `src/support_python/__main__.py`.
- In `support_python/cli.py`, delete `main`, `_build_demo_parser`, `format_support_message`, the demo `PROG`,
  `DESCRIPTION`, and `ACTIONS` constants, and the `__main__` block.
  Drop them from `__all__` and from `support_python/__init__.py`.
- Keep `ToolHarness`, `Action`, `get_full_version`, `resolve_build_metadata`, and the argparse helpers; T0044 removes the helpers.
- Grep `src`, `tests`, and `scripts` for any other use of the removed names and fix it.
- Delete `scripts/processes.py`, `scripts/lint-markdown.py`, `scripts/agent-files.py`, `scripts/backup-git-repos.py`,
  `scripts/_harness.py`, and `scripts/_tool_common.py`.
- Delete `tests/test_lint_markdown_script.py`, `tests/test_agent_files_script.py`, and `tests/test_tool_common.py`.
  Move any still-relevant subprocess case into `tests/test_console_scripts.py`, running the installed console script.
- Keep `scripts/_cli_common.py`; `bootstrap-dev-environment.py` and `devops.py` still use it.

### README
- Replace every `support-python ...` and `python scripts/<tool>.py` usage with the four commands.
- Add an "Installing the command-line tools" section covering:
  - `pipx install "git+https://github.com/gpellicciotta/support.python.git@v<version>"`
  - `uv tool install "git+https://github.com/gpellicciotta/support.python.git@v<version>"`
  - `pip install --user "git+https://github.com/gpellicciotta/support.python.git@v<version>"`
  - `python scripts/install-from-github-release.py <version> --global`
- Note that installing the package installs all tools together.

### Declared Files
- pyproject.toml
- src/support_python/cli.py
- src/support_python/__init__.py
- src/support_python/agent_files.py
- tests/test_console_scripts.py
- tests/test_cli.py
- README.md
- CHANGELOG.md
- docs/requirements.md
- docs/agent-files.md
- docs/markdown-lint.md

### Tests
- Unit: the installed distribution's console scripts are exactly `processes`, `agent-files`, `lint-markdown`, and `git-repository-backup`.
- Unit: importing `support_python.__main__` raises `ModuleNotFoundError`, and `support_python.cli` has no `main`.
- Unit: the agent-files banner and usage name read `agent-files`.
- Integration: after `.venv/Scripts/pip install -e ".[dev]"`, each tool's `version` action exits 0 and prints its banner.
- Integration: installed `lint-markdown check --offline docs` runs and exits 0 or 1 with an issue report.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration commands above.
Size estimate: 11 files, 350 lines.
Size note: above the typical line because every document naming the removed command must change with it.
