### Command-Line Interface
```text
lint-markdown check [PATH...] [--format text|json] [--rules IDS] [--profile NAME] [--config PATH] [--offline] [--exclude GLOB]
lint-markdown fix [PATH...] [--dry-run] [--rules IDS] [--profile NAME] [--config PATH] [--offline] [--exclude GLOB]
lint-markdown help [--verbose]
lint-markdown version
```
- `--fix` becomes an unknown option, exiting 2.
- `fix --dry-run` lists every file and issue it would fix, writes nothing, and exits 0.
- `check --format json` prints one object on stdout:
  `{"files_checked": N, "issues": [{"path", "line", "column", "rule_id", "rule_name", "message", "fixable"}]}`.
- In JSON mode, stdout carries only the JSON document.

### Config Discovery
- Set `DEFAULT_CONFIG_FILENAME = ".lint-markdown.json"` in `markdown/profiles.py`, with `LEGACY_CONFIG_FILENAME = ".markdown-lint.json"`.
- Look both up in today's locations; the new name wins.
- Reading only the legacy file logs one `WARN` asking to rename it, noting removal in v3.0.0.

### Declared Files
- src/support_python/tools/lint_markdown.py
- src/support_python/markdown/profiles.py
- src/support_python/markdown/lint.py
- tests/tools/test_lint_markdown.py
- tests/test_markdown_profiles.py
- docs/tools/lint-markdown.md
- README.md
- CHANGELOG.md

### Tests
- Unit: `--fix` exits 2; `fix --dry-run` writes nothing and reports planned fixes.
- Unit: `check --format json` output parses and lists issues with the documented keys.
- Unit: config discovery covers the new name, legacy-only with a warning, and both present.
- Integration: installed `lint-markdown check --offline --format json docs` prints parseable JSON.
- Integration: in a temporary directory holding only `.markdown-lint.json` that disables a rule, `lint-markdown check` warns and honors it.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration commands above.
Size estimate: 8 files, 300 lines.
