### Declared Files
- src/support_python/tools/lint_markdown.py
- src/support_python/markdown/profiles.py
- tests/tools/test_lint_markdown.py
- tests/test_markdown_profiles.py
- docs/tools/lint-markdown.md
- CHANGELOG.md

### Tests
- Unit: `LINT_MARKDOWN_PROFILE=dev-guidelines` beats the project file and loses to `--profile default`.
- Unit: A user-file `disable` list is replaced, not merged, by a project-file `disable` list.
- Unit: Unknown keys in `.lint-markdown.json` are ignored and listed only in `--debug` output.
- Integration: Run the installed `lint-markdown config list --format json` and `lint-markdown check` in a temporary project with user and project files.

Completion check: `.venv/Scripts/python -m pytest tests/tools/test_lint_markdown.py tests/test_markdown_profiles.py` plus the integration scenario above.
Size estimate: 6 files, 400 lines

### Notes
- Settings: `profile`, `rules`, `enable`, `disable`, `historical-task-exemptions`, `exclude`, `plugins`, `offline` (boolean), and `timeout` (duration).
- `--rules`, `--exclude`, and `--plugin` stay repeatable options that replace the file values.
- Library callers of `load_profile` and `MarkdownLinter` keep working unchanged.
- Follow [configuration-guidelines.md](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md).
