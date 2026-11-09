### Engine and CLI Split
- CLI, moving to `support_python.tools.lint_markdown`: `TOOL_NAME`, `build_harness`, `main`, action handlers,
  argument parsing, usage and example constants, and console output formatting tied to the CLI.
- Engine, staying in `support_python.markdown.lint`: `MarkdownLinter`, `LintIssue`, file collection, fixing, and
  reporting functions usable without argparse.
- The engine imports neither `argparse` nor `support_python.cli`.
- `markdown/registry.py` and `markdown/rules.py` import `LintIssue` from `support_python.markdown.lint`, keeping
  lazy imports where needed to avoid import cycles.
- Point the console script at `lint-markdown = "support_python.tools.lint_markdown:main"`.
- Leave no shim at `support_python.markdown_lint`; list the move as a breaking change.

Mechanical command: `git mv src/support_python/markdown_lint.py src/support_python/markdown/lint.py`
Mechanical command: `git mv docs/markdown-lint.md docs/tools/lint-markdown.md`

### Declared Files
- src/support_python/markdown/lint.py
- src/support_python/tools/lint_markdown.py
- src/support_python/markdown/__init__.py
- src/support_python/markdown/registry.py
- src/support_python/markdown/rules.py
- src/support_python/__init__.py
- pyproject.toml
- tests/test_markdown_lint.py
- tests/tools/test_lint_markdown.py
- docs/tools/lint-markdown.md
- docs/index.md
- README.md
- CLAUDE.md
- CHANGELOG.md

### Tests
- Unit: engine tests in `tests/test_markdown_lint.py` pass importing only `support_python.markdown.lint`.
- Unit: importing `support_python.markdown.lint` loads neither `argparse` nor `support_python.cli` modules it did not need before.
- Unit: CLI tests in `tests/tools/test_lint_markdown.py` pass against `support_python.tools.lint_markdown.main`.
- Integration: installed `lint-markdown check --offline docs README.md CHANGELOG.md` keeps its pre-split exit code and issue count.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration command above.
Size estimate: 14 files, 600 lines.
Size note: moved CLI code counts twice, as removed and added lines; a further split would leave the module half-moved.
