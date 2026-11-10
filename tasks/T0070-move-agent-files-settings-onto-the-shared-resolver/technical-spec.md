### Declared Files
- src/support_python/tools/agent_files.py
- src/support_python/tools/agent_files_config.py
- tests/tools/test_agent_files.py
- docs/tools/agent-files.md
- CHANGELOG.md

### Tests
- Unit: `AGENT_FILES_MARKER=custom` beats `.agent-files.json` and loses to `--marker other`.
- Unit: A user-file `tools` entry for `codex-cli` and a project-file entry for `claude-code` both apply.
- Unit: Malformed `.agent-files.json` warns once naming the file and falls back to defaults.
- Integration: Run the installed `agent-files config list --format json` and `agent-files sync --dry-run` with a temporary `HOME` and project file.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_agent_files.py` plus the integration scenario above.
Size estimate: 5 files, 400 lines

### Notes
- Settings: `repo-root`, `digest-path`, `skills-dir`, `marker`, `marker-begin`, `marker-end`, `manifest-source`, `manifest-name`, `legacy-skill-names`, `replace-tools`, `tools`.
- Tests must redirect `HOME`, `APPDATA`, and `XDG_CONFIG_HOME`; never touch the real `~/.claude/`.
- Follow [configuration-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md).
