## Walkthrough & Validation

### Key Changes
- Copied dev-guidelines `scripts/lint-markdown.py` into `src/support_python/markdown_lint.py` and fixed imports to use `support_python.cli.ToolHarness` and `support_python.logging.ToolLogger`.
- Derived `REPO_ROOT` from `find_project_root(Path.cwd())`, resolved root-relative `/...` links in `MD014` against `current_project_root`, and resolved sibling repository GitHub links in `MD018` against `_resolve_workspace_root(current_project_root)` (matching `repo_name == base_root.name` for the current repo and `workspace_root / repo_name` for siblings).
- Moved UTF-8 stream reconfiguration inside `markdown_lint.main()`.
- Copied dev-guidelines `scripts/tests/test_lint_markdown.py` into `tests/test_markdown_lint.py`, made `test_local_dev_guidelines_github_url_resolves_locally`, `test_backticked_repo_file_flags_md019`, and `TestChangelogReleasedHeadings` self-contained via temporary workspace/project fixtures, changed `test_script_entry_point_checks_readme_offline` to lint `LICENSE.md`, and added root-relative `MD014` and `support-python lint markdown` CLI subcommand tests.
- Registered the `lint` action (`support-python lint markdown [paths] [--fix] [--offline]`) in `src/support_python/cli.py`.
- Documented `support-python lint markdown` in `README.md`, `docs/index.md`, and `CHANGELOG.md` (bumping to `v1.0.19-pre` in `CHANGELOG.md` and `pyproject.toml`).

### Red-Phase Test Failure Proof
Command: `python -m pytest tests/test_markdown_lint.py -q -k "TestRuleMD018 or TestRuleMD019 or TestDiscoverMarkdownFilesGitIgnore or TestChangelogReleasedHeadings"`
Exit code: `1`
```text
[... 42 lines omitted ...]
=========================== short test summary info ===========================
FAILED tests/test_markdown_lint.py::TestRuleMD018ValidExternalLinks::test_local_dev_guidelines_github_url_resolves_locally
FAILED tests/test_markdown_lint.py::TestDiscoverMarkdownFilesGitIgnore::test_root_relative_link_resolves_against_project_root
2 failed, 21 passed, 93 deselected in 1.97s
```

### Green-Phase Test Suite and Linter Verification
Command: `python -m pytest tests/test_markdown_lint.py -q`
Exit code: `0`
```text
........................................................................ [ 62%]
............................................                           [100%]
116 passed, 2 subtests passed in 4.26s
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
.............................................................            [100%]
654 passed, 3 skipped, 52 subtests passed in 146.84s (0:02:26)
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

Command: `python -c "import sys; from support_python.cli import main; sys.exit(main(['lint', 'markdown', '--offline']))"` (in `dev-guidelines`)
Exit code: `0`
```text
Starting lint-markdown v1.0.19-pre+ec21004 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\dev-guidelines
All 54 markdown files passed linting.
Finished lint-markdown check in 1.2s with status: succeeded
```

Command: `python -m ruff check . ; python -m ruff format --check .`
Exit code: `0`
```text
All checks passed!
81 files already formatted
```
