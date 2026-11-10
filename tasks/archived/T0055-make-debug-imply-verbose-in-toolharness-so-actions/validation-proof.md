## Walkthrough & Validation

### Red phase
`.venv/Scripts/python -m pytest -q tests/test_cli.py -k DebugImpliesVerbose` (exit 1, before the fix):
```text
tests\test_cli.py:363: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_cli.py::ToolHarnessDebugImpliesVerboseTests::test_debug_alone_sets_args_verbose
FAILED tests/test_cli.py::ToolHarnessDebugImpliesVerboseTests::test_debug_option_help_mentions_verbose
SUBFAILED(argv=['help', '--debug']) tests/test_cli.py::ToolHarnessDebugImpliesVerboseTests::test_help_debug_matches_help_verbose
FAILED tests/test_cli.py::ToolHarnessDebugImpliesVerboseTests::test_help_debug_matches_help_verbose
FAILED tests/test_cli.py::ToolHarnessDebugImpliesVerboseTests::test_log_level_wins_threshold_but_debug_still_implies_verbose
5 failed, 1 passed, 17 deselected, 2 subtests passed in 0.46s
```

### Green phase
`.venv/Scripts/python -m pytest -q` (exit 0):
```text
1080 passed, 3 skipped, 141 subtests passed in 125.60s (0:02:05)
```

`.venv/Scripts/ruff check src tests` (exit 0):
```text
All checks passed!
```

### Integration
Installed `lint-markdown check --offline {{flag}} clean.md` on a clean file; banner and DEBUG lines filtered out.
```text
== --verbose (after)
OK: clean.md
All 1 markdown files passed linting.
== --debug (after)
OK: clean.md
All 1 markdown files passed linting.
== --debug (before, change stashed)
All 1 markdown files passed linting.
```

### Automated integration test (added after review)
`.venv/Scripts/python -m pytest -q tests/tools/test_lint_markdown.py -k debug_alone`, with `cli.py` stashed and then restored:
```text
1 failed, 39 deselected in 0.47s
1 passed, 39 deselected in 0.37s
```
