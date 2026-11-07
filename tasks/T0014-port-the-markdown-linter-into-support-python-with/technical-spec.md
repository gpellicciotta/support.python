### Declared Files
- src/support_python/markdown_lint.py
- src/support_python/cli.py
- tests/test_markdown_lint.py
- README.md
- docs/index.md
- pyproject.toml
- CHANGELOG.md

### Tests
- Unit: all cases from dev-guidelines `test_lint_markdown.py` pass unchanged against `support_python.markdown_lint`.
- Integration: `support-python lint markdown --offline` run in dev-guidelines prints the same issue list and exit code as `python scripts/lint-markdown.py check --offline`.

Completion check: `python -m pytest tests/test_markdown_lint.py -q`
Size estimate: 7 files, 2860 lines
Size note: Above the typical line because two files are mechanical copies of dev-guidelines lint-markdown.py (1,599 lines) and test_lint_markdown.py (1,232 lines); hand-written changes are under 80 lines.
