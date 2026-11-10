## Walkthrough & Validation
Added `support_python.config.normalize_config_keys`, used by agent-files, lint-markdown profiles, and git-repository-backup.

Failing tests before implementation: 4 failed (`test_markdown_profiles` x2, `AgentFilesKebabConfigTests`, `SnakeCaseConfigKeyTests`); `tests/test_config.py` failed on import.

Command: `pytest tests/test_config.py tests/test_markdown_profiles.py tests/tools -q`, then `ruff check src tests`, `ruff format --check src tests`

```text
....................................................... [ 70%]
...............................................................................................                       [100%]
321 passed, 89 subtests passed in 60.92s (0:01:00)
All checks passed!
124 files already formatted
```
