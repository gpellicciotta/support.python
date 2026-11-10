# Kebab-case configuration keys in support.python tools

## Technical Specifications
### Evidence
- `agent-files` reads keys such as `digest_path`, `skills_dir`, and `fallback_paths` from `.agent-files.json`.
- `lint-markdown` reads keys such as `disabled_rules` and `enabled_rules` from `.lint-markdown.json`.
- `git-repository-backup` reads `~/.config/git-repository-backup/config.json`.
- The tool docs under `docs/tools/` show snake_case keys in their configuration examples.

### Required Behavior
- Every tool accepts each configuration key in kebab-case or snake_case, with identical effect.
- A file setting the same key in both spellings uses the kebab-case value and logs one warning.
- Docs, examples, and any configuration a tool writes use kebab-case keys.
- `--config` files follow the same rules as discovered files.
- No deprecation warning for snake_case keys, because the guidelines accept both spellings permanently.

### Design Decisions
- **[Decided]** Normalize keys in one shared loader used by every tool, not in each tool's lookups.
- **[Decided]** Keep Python attribute and parameter names in snake_case; only file keys change.

### Out of Scope
- JSON field names in `--format json` output.
- The configuration file locations, which a separate decision may change.

### Tests
- Unit: The shared loader returns the same settings for a kebab-case file and its snake_case twin.
- Unit: A file with `digest-path` and `digest_path` uses the kebab-case value and logs one warning.
- Unit: Each tool's documented example configuration loads without warnings.
- Integration: `agent-files check --config` with a kebab-case file behaves like the same run with a snake_case file.

### Declared Files
- The shared configuration loader under `src/support_python/`
- `src/support_python/tools/agent_files_config.py`
- `src/support_python/tools/lint_markdown.py`
- `src/support_python/tools/git_repository_backup.py`
- Tests for the loader and each tool
- `docs/tools/agent-files.md`, `docs/tools/lint-markdown.md`, and `docs/tools/git-repository-backup.md`
- `CHANGELOG.md`
