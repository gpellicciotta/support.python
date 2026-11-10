## Walkthrough & Validation

### Completion check
```text
$ .venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/tutorials docs/tools/processes.md
All 14 markdown files passed linting.
(exit code 0)
```

### Removed README anchors
```text
$ grep -rn "README.md#(git-repository-helpers|locking|process-hierarchy|atomic-text|markdown-table|markdown-linter|duration-and|task-rate)" --include=*.md . (excluding .plan and .venv)
exit 1
```

### Snippets executed from scratch directories
```text
ok git-helpers.md 0 (outside a repository: "Repository status could not be queried")
ok markdown.md 0
ok markdown.md 1 (printed "3:17 MD011 Line contains trailing whitespace")
ok durations-and-rate-limiting.md 0
ok durations-and-rate-limiting.md 1
ok files-and-locking.md 0
ok files-and-locking.md 1
ok process-management.md 0 (safe_kill skipped the protected current PID)
```
