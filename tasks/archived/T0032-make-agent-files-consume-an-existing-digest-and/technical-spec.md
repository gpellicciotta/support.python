### Changes
- Remove `get_digest_generator`, the stale-source detection, and the dev-guidelines constants and helpers
  (`guidelines/agent-digest.md`, `skills/`, `DIGEST_PATH`, `SKILLS_DIR`, and `_resolve_repo_root` defaults).
- New defaults match `agent-digest` (T0020): `agent-digest.md` and `agent-skills/` under the project root,
  or under the config file's directory when a config sets no paths.
- Missing digest: `sync` and `check` log an error naming the expected path and suggesting
  `agent-digest generate <PATH>... --digest <path> --skills-dir <dir>`, then exit 1.
- A missing skills directory means no skills, as today.

### Declared Files
- src/support_python/tools/agent_files.py
- src/support_python/tools/agent_files_config.py
- tests/tools/test_agent_files.py
- docs/tools/agent-files.md
- README.md
- CHANGELOG.md

### Tests
- Unit: `sync` and `check` never import or call `support_python.tools.agent_digest`.
- Unit: defaults resolve to `<root>/agent-digest.md` and `<root>/agent-skills`; flags and config keys override them.
- Unit: a missing digest exits 1 with a hint naming `agent-digest generate`.
- Integration: in a temporary project, installed `agent-digest generate notes --digest agent-digest.md --skills-dir agent-skills`,
  then `agent-files check` with `.agent-files.json` routing tool targets into temporary directories exits 1,
  and exits 0 after `agent-files sync`.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration scenario above.
Size estimate: 6 files, 300 lines.
