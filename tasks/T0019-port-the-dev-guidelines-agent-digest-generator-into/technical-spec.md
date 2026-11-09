### Source
- Script: `git -C {{dev-guidelines}} show 38e0de0:scripts/generate-agent-digest.py`.
- Tests: `git -C {{dev-guidelines}} show 38e0de0:scripts/tests/test_generate_agent_digest.py`.
- Keep behavior identical: actions `generate`, `check`, `validate`, and the hardcoded `guidelines/` and `skills/` layout under the project root.
- Resolve the project root with `find_project_root(Path.cwd())`, as `support_python.agent_files` does.
- Replace the `scripts/lib` imports (`tool_common`, `harness`) with `support_python.cli.ToolHarness` and `support_python.logging`.
- Some ported tests read dev-guidelines' real `guidelines/` and `skills/`; copy those trees from commit `38e0de0` into `tests/fixtures/agent_digest/`.

### CLI Wiring
- Add an `agent-digest = "support_python.tools.agent_digest:main"` entry under `[project.scripts]` in `pyproject.toml`.
- Add no `support-python` action and no `scripts/` wrapper; ADR-0003 removed both.
- Rename the tool name in banners and usage from `generate-agent-digest` to `agent-digest`.
- Make `tools.agent_files.get_digest_generator` import `support_python.tools.agent_digest` and stop loading `scripts/generate-agent-digest.py`.

### Declared Files
- src/support_python/tools/agent_digest.py
- src/support_python/tools/agent_files.py
- pyproject.toml
- tests/tools/test_agent_digest.py
- README.md
- CHANGELOG.md

### Tests
- Unit: all cases from dev-guidelines `test_generate_agent_digest.py` pass against `support_python.agent_digest`.
- Unit: `agent_files.get_digest_generator` returns the packaged module without a `scripts/generate-agent-digest.py` file.
- Unit: installed `agent-digest version` prints the `agent-digest` banner and exits 0.
- Integration: in a dev-guidelines worktree at commit `38e0de0`, `agent-digest check` and `agent-digest validate` exit 0.
- Integration: in that worktree, `agent-digest generate` leaves `git status --short` empty.

Completion check: `python -m pytest tests -q`, plus the dev-guidelines integration commands above.
Size estimate: 6 files, 120 hand-written lines plus mechanical copies.
Mechanical command: `git -C {{dev-guidelines}} show 38e0de0:scripts/generate-agent-digest.py > src/support_python/tools/agent_digest.py`
Mechanical command: `git -C {{dev-guidelines}} show 38e0de0:scripts/tests/test_generate_agent_digest.py > tests/tools/test_agent_digest.py`
Mechanical command: `git -C {{dev-guidelines}} archive 38e0de0 guidelines skills | tar -x -C tests/fixtures/agent_digest`
