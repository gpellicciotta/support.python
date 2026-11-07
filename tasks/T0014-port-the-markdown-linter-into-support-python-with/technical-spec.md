### Declared Files
- src/support_python/markdown_lint.py
- src/support_python/cli.py
- tests/test_markdown_lint.py
- CHANGELOG.md

### Tests
- Unit: all cases from dev-guidelines `test_lint_markdown.py` pass unchanged against `support_python.markdown_lint`.
- Integration: `support-python lint markdown --offline` run in dev-guidelines prints the same issue list and exit code as `python scripts/lint-markdown.py check --offline`.

Completion check: `python -m pytest tests/test_markdown_lint.py -q`
