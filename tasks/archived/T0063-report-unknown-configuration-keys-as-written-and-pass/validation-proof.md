## Walkthrough & Validation
Unknown keys now print in kebab-case; clash warnings use the tool logger.

Five new tests failed before the change and pass after it.

Command: `pytest tests/test_markdown_profiles.py tests/tools/test_agent_files.py -q`, `ruff check src tests`

```text
.....................................................                 [100%]
114 passed, 14 subtests passed in 4.00s
All checks passed!
```
