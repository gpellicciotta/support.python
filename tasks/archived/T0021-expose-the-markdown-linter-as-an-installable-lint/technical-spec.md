### Declared Files
- pyproject.toml
- tests/test_lint_markdown_script.py
- docs/markdown-lint.md
- README.md
- CHANGELOG.md

### Tests
- Unit: `importlib.metadata.entry_points(group="console_scripts")` holds `lint-markdown` with value `support_python.markdown_lint:main`.
- Integration: in a fresh virtual environment with the package installed, `lint-markdown version` prints the `lint-markdown v` banner, and `lint-markdown check --offline` exits 0 on a clean file and non-zero on a bad one.

Completion check: `python -m pytest tests -q`, plus the integration commands above.
Size estimate: 5 files, 40 lines.
