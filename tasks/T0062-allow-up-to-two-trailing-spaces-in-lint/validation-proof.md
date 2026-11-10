## Walkthrough & Validation

MD011 allows up to two trailing spaces; `fix` trims longer runs to two and removes tabs.

### Tests
Command: `python -m pytest tests/test_markdown_lint.py tests/test_markdown_profiles.py tests/tools/test_lint_markdown.py -q` (exit 0)

```text
........................................................................ [ 52%]
.................................................................      [100%]
137 passed, 2 subtests passed in 3.08s
```

### Lint
Command: `ruff check src tests` (exit 0)

```text
All checks passed!
```

### Review
Agent review approved by a read-only reviewer subagent (137 tests, ruff check and format pass).
