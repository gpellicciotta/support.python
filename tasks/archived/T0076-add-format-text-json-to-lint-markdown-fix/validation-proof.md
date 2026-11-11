# T0076 Validation Proof

## Red phase
Command: `python -m pytest tests/tools/test_lint_markdown.py -q -k "fix_format_json or fix_dry_run_format or action_specific"`
```
FAILED test_fix_format_json_failures_keep_stdout_clean
FAILED test_fix_format_json_clean_directory_exits_zero_with_empty_lists
FAILED test_fix_format_json_without_markdown_files_emits_empty_document
FAILED test_fix_dry_run_format_json_lists_planned_fixes_and_writes_nothing
FAILED test_fix_format_json_lists_fixed_files_and_remaining_issues
SUBFAILED(action="'fix'") test_action_specific_help_shows_only_target_action
6 failed, 1 passed, 1 subtests passed
```
Cause: `fix` did not accept `--format`.

## Green phase
Command: `PYTHONPATH=src python -m pytest tests -q`
```
1195 passed, 5 skipped, 181 subtests passed in 12.36s
```
`ruff check src tests`: `All checks passed!`; `ruff format`: `130 files left unchanged`.
`lint-markdown check --offline docs/tools/lint-markdown.md CHANGELOG.md`: `All 2 markdown files passed linting.`

## Integration
Command: `python -m support_python.tools.lint_markdown fix --format json --offline {{tmp-dir}}` on a file with `*` bullet, trailing spaces, and an H1 to H3 skip.
- Exit code `1`; `stdout` held one JSON object with `fixed` (MD011, MD005) and `issues` (MD001).
- `stderr` held `Auto-fixed formatting issues in 1 file.` and the lint warning; the file was rewritten.
