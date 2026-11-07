## Walkthrough & Validation

### Key Changes
- Copied dev-guidelines `scripts/lint-markdown.py` into `src/support_python/markdown_lint.py` unchanged apart from importing `ToolHarness` and `ToolLogger` from `support_python.cli` and `support_python.logging`, and moving UTF-8 stream reconfiguration into `main()`.
- Copied dev-guidelines `scripts/tests/test_lint_markdown.py` into `tests/test_markdown_lint.py`, updated imports to reference `support_python.markdown_lint`, and added CLI dispatch tests for `support-python lint markdown`.
- Registered the `lint` action (`support-python lint markdown [paths] [--fix] [--offline]`) in `src/support_python/cli.py`.
- Updated `CHANGELOG.md` (bumping to `v1.0.19-pre`), `pyproject.toml`, and `docs/index.md`.

### Red-Phase Test Failure Proof
Command: `python -m pytest tests/test_markdown_lint.py -q`
Exit code: `1`
```text
[... 85 lines omitted ...]
=========================== short test summary info ===========================
FAILED tests/test_markdown_lint.py::TestEndToEnd::test_support_python_lint_markdown_cli_subcommand
1 failed, 114 passed, 2 subtests passed in 5.29s
```

### Green-Phase Test Suite and Linter Verification
Command: `python -m pytest tests/test_markdown_lint.py -q`
Exit code: `0`
```text
........................................................................ [ 62%]
...........................................                            [100%]
115 passed, 2 subtests passed in 9.11s
```

Command: `python -m pytest tests -q`
Exit code: `0`
```text
..................................................... [  8%]
........................................... [ 14%]
...................................................................... [ 25%]
.....................................................................s.. [ 36%]
........................................................................ [ 47%]
...................................s......s............................. [ 58%]
........................................................................ [ 69%]
...................................................................... [ 79%]
........................................................................ [ 90%]
............................................................             [100%]
653 passed, 3 skipped, 52 subtests passed in 241.43s (0:04:01)
```

Command: `python scripts/lint-markdown.py check --offline` (in `dev-guidelines`)
Exit code: `0`
```text
Starting lint-markdown v1.12.9-pre+5f5408e with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\dev-guidelines
All 54 markdown files passed linting.
Finished lint-markdown check in 1.3s with status: succeeded
```

Command: `python -m support_python.cli lint markdown --offline` (in `dev-guidelines`)
Exit code: `0`
```text
Starting lint-markdown v1.0.19-pre+37cd186 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\dev-guidelines
All 54 markdown files passed linting.
Finished lint-markdown check in 1.1s with status: succeeded
```

Command: `python -m ruff check . ; python -m ruff format --check .`
Exit code: `0`
```text
All checks passed!
81 files already formatted
```
