### Command-Line Interface
```text
agent-files list [--format text|json] [--config PATH]
agent-files sync [TOOL...] [--dry-run] [--no-prune] [existing sync options]
agent-files check [TOOL...] [--format text|json] [existing sync options]
agent-files review [TOOL...] [--timeout SECONDS]
agent-files help [--verbose]
agent-files version
```
- `update` and `diff` become unknown actions, exiting 2.
- `check` writes nothing, exits 0 when every tool is up to date, and 1 otherwise.
- `list --format json`: one array of objects with the text table's columns as snake_case keys,
  for example `command`, `available`, `executable`, `version`, `instructions_file`, and `skills_dir`.
- `check --format json`: one array with an object per tool holding `tool`, `status`
  (`up-to-date`, `changes-pending`, or `unavailable`), and a `changes` list derived from the existing diff data.
- In JSON mode, stdout carries only the JSON document, as `processes list --format json` does.

### Config Discovery
- Set `DEFAULT_CONFIG_FILENAME = ".agent-files.json"`, looked up where `agent-files.json` is looked up today.
- When only `agent-files.json` exists, read it and log one `WARN` asking to rename it, noting removal in v3.0.0.
- When both exist, use `.agent-files.json` and warn that the legacy file is ignored.

### Declared Files
- src/support_python/tools/agent_files.py
- src/support_python/tools/agent_files_config.py
- tests/tools/test_agent_files.py
- docs/tools/agent-files.md
- README.md
- CHANGELOG.md

### Tests
- Unit: help lists exactly `list`, `sync`, `check`, `review`, `help`, and `version`; `update` and `diff` exit 2.
- Unit: `check` exits 0 when clean and 1 with pending changes, writing nothing, against temporary tool targets.
- Unit: `list` and `check` JSON output parses and contains the documented keys.
- Unit: config discovery covers `.agent-files.json`, legacy-only with a warning, and both present.
- Integration: in a temporary project with a fixture digest, skills, and `.agent-files.json` routing every tool target
  into temporary directories, installed `agent-files sync` then `agent-files check` exit 0,
  and `check` exits 1 after a target file is edited.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration commands above.
Size estimate: 6 files, 350 lines.
