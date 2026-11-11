### Declared Files
- docs/specs/agent-files-config.md
- docs/specs/lint-markdown-config.md
- docs/specs/git-repository-backup-config.md
- docs/specs/agent-digest-front-matter.md
- docs/specs/json-output.md
- docs/index.md
- AGENTS.md
- docs/tools/{{tool}}.md (five tool pages gain spec links)

Completion check: `.venv/Scripts/lint-markdown check --offline docs AGENTS.md` exits 0.
Size estimate: 12 files, 700 lines
Size note: Each spec is independent, but one pass keeps naming and structure consistent across all formats.

### Notes
- Write it after the configuration (T0068-T0070) and `--format` (T0074-T0078) tasks, so the specs describe final formats.
- State in the JSON spec that renaming or removing a field is a breaking change.
- Follow [project-setup-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/project-setup-guidelines.md) naming rules for `docs/specs/`.
