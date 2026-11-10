### Declared Files
- src/support_python/cli.py
- src/support_python/capture.py
- src/support_python/devops/cli.py
- src/support_python/tools/__init__.py
- src/support_python/tools/agent_files.py
- src/support_python/tools/agent_digest.py
- src/support_python/tools/lint_markdown.py
- src/support_python/tools/processes.py
- src/support_python/tools/git_repository_backup.py
- scripts/devops.py
- tests/test_cli.py
- tests/test_devops_cli.py
- tests/test_capture.py
- tests/test_console_scripts.py
- tests/tools/test_lint_markdown.py
- docs/tutorials/cli-harness-and-logging.md
- docs/migration-v2.md
- CHANGELOG.md

### Changes
- `APP_AUTHOR: str = ""` and `COPYRIGHT: str = ""`; their doc comments tell consumers to pass their own.
- The banner is `{name} v{version}`, plus ` - {copyright}` only when `copyright` is non-empty.
- `capture.py` builds `Copyright (c) {author}` only when `author` is non-empty, and an empty copyright otherwise.
- `support_python/tools/__init__.py` defines `TOOLS_COPYRIGHT = "Copyright (c) Giovanni Pellicciotta"`.
  - It matches `authors` in pyproject.toml and stays out of the package root exports.
- Each bundled tool passes `copyright=TOOLS_COPYRIGHT` to its `ToolHarness`.
- `DevopsCli(..., copyright: str = COPYRIGHT)` forwards its argument to `ToolHarness`; `scripts/devops.py` passes `TOOLS_COPYRIGHT`.
- Update the module docstring at cli.py:5 to describe the optional suffix.
- **[Decided]** Bundled tools keep their banner; only the library default becomes empty.

### Tests
- Unit: a `ToolHarness` with the default copyright prints `name vX` without a ` - ` suffix in its version and help headers.
- Unit: an explicit copyright still prints `name vX - Copyright (c) Someone`; `DevopsCli` forwards its argument.
- Unit: view capture with an empty author prints no copyright suffix.
- Integration: run each installed console script with `--version`.
  - Assert each banner still ends with `Copyright (c) Giovanni Pellicciotta`.

Completion check: `.venv/Scripts/python -m pytest tests/test_cli.py tests/test_devops_cli.py tests/test_capture.py tests/test_console_scripts.py` plus `python scripts/devops.py check`.
Size estimate: 18 files, 260 lines
Size note: Each bundled tool needs a one-line wiring change; splitting would ship the tools without their banner.

### Notes
- Breaking v2 change for consumers that rely on the default banner: record it in migration-v2.md and CHANGELOG.md.
- auth and counters.server import `APP_AUTHOR` for their banners; their backlog tasks cover passing their own.
