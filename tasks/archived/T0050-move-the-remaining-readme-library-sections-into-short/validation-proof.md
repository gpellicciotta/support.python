## Walkthrough & Validation

### Completion check
```text
$ .venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/tutorials
All 8 markdown files passed linting.
(exit code 0)
```

### Removed README anchors
```text
$ grep -rn "README.md#(shared-cli|cli-logging|common-script|rest-client|view-capture|sql-snapshot|models-and)" --include=*.md . (excluding .plan and .venv)
exit 1
```

### Snippets executed from a scratch directory
```text
ok rest-clients.md 1 (errors)
ok rest-clients.md 2 (models)
ok cli-harness-and-logging.md 0 (harness, tables, tokens)
ok cli-harness-and-logging.md 1 (logging)
ok script-utilities.md 0
```
The network, capture, and SQL snippets were not executed; they need a server, a browser, or a dump.
