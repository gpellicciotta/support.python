## Walkthrough & Validation

### Completion check
```text
$ .venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/migration-v2.md docs/tutorials
All 4 markdown files passed linting.
(exit code 0)
```

### Removed README anchor
```text
$ grep -rn "README.md#devops" --include=*.md . (excluding .plan and .venv)
(no matches, exit code 1)
```

### Documented symbols are exported
```text
$ .venv/Scripts/python -c "<hasattr check over 29 documented names>"
missing devops: []
missing root: []
(exit code 0)
```
