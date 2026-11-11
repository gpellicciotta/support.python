### Declared Files
- src/support_python/tools/agent_files.py
- src/support_python/tools/agent_files_config.py
- tests/tools/test_agent_files.py
- docs/tools/agent-files.md
- CHANGELOG.md

### Tests
- Unit: Skills-only sync into a temporary home exits 0 without a digest and leaves instruction files untouched.
- Integration: Run `agent-files sync --skills-only` twice on a temporary home, then remove a skill, then add a legacy directory.

Completion check: `pytest tests/tools/test_agent_files.py` and `ruff check src tests`
Size estimate: 5 files, 350 lines

### Required Behaviors
- Source: a skills directory of `{{name}}/SKILL.md` trees; plan points it at the skills inside its installed package.
- Targets: claude-code `~/.claude/skills`, codex `~/.agents/skills`, antigravity `~/.gemini/config/skills`; the caller chooses which tools, since plan installs only for agents it finds ready.
- Report per skills directory which skills were installed, unchanged, skipped, or pruned.
- Install only missing or outdated skills, and skip any skill directory that another tool owns.
- Ownership manifest: configurable file name `.plan-skills.json` and source `plan`; read plan's existing manifests (`schema_version` 1, `source`, `version`, `skills`) and record the caller's version.
- Prune owned skills that are no longer bundled, and leave extra files inside owned skill directories.
- Retire legacy directories: remove the owned skills and the manifest from `~/.gemini/antigravity-cli/skills`, and leave other tools' skills there.
- Support `--dry-run`: report every planned change and write nothing.
- The library function takes explicit paths, returns results, and neither exits the process nor requires a logger.
- Never touch instruction files or require a digest in skills-only mode.
