### Declared Files
- src/support_python/tools/lint_markdown.py
- tests/tools/test_lint_markdown.py
- docs/tools/lint-markdown.md
- CHANGELOG.md

### Tests
- Unit: `fix --format json` lists fixed files and remaining issues in the `check --format json` issue shape.
- Unit: `fix --dry-run --format json` lists planned fixes and writes nothing.
- Integration: Run the installed `lint-markdown fix --format json` on a temporary file with fixable and unfixable issues.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_lint_markdown.py` plus the integration scenario above.
Size estimate: 4 files, 200 lines

### Notes
- Name JSON fields in lowercase kebab-case, consistent with the tool's existing JSON documents.
- Treat every field as a compatibility contract; T0081 later specifies the documents.
- Follow [cli-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/cli-guidelines.md).
