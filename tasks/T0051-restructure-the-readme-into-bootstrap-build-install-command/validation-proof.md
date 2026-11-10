## Walkthrough & Validation

### Completion check
```text
$ .venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/devops.md docs/tools docs/tutorials
All 19 markdown files passed linting.
(exit code 0)
```

### Standard tool options claimed in README
```text
processes: help=0 version=0 --version=0 -h=0 verbose-in-help=3
agent-files: help=0 version=0 --version=0 -h=0 verbose-in-help=3
agent-digest: help=0 version=0 --version=0 -h=0 verbose-in-help=3
lint-markdown: help=0 version=0 --version=0 -h=0 verbose-in-help=3
git-repository-backup: help=0 version=0 --version=0 -h=0 verbose-in-help=3
```

### README-only tool details already in docs/tools
```text
$ grep -c "set-password|restore|backup [" docs/tools/git-repository-backup.md  -> 8
$ grep -c "skill-index" docs/tools/agent-digest.md                            -> 3
$ grep -c "lint-markdown rules|--plugin" docs/tools/lint-markdown.md         -> 7
$ grep -c "markdown-lint.json" docs/tools/lint-markdown.md                    -> 1
```
The lint-markdown check validates every relative link in README.md.
