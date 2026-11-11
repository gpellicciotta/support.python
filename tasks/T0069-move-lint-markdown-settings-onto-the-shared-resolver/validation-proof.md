# T0069 Validation Proof

## Red phase
Command: `python -m pytest tests/tools/test_lint_markdown.py -k SharedSettings -q -n0`

```text
FAILED test_alias_keys_resolve_to_their_setting
FAILED test_config_list_names_every_setting
FAILED test_config_set_user_and_system_files_and_rejects_bad_values
FAILED test_config_targets_project_file_by_default
FAILED test_environment_list_replaces_the_project_list_as_a_whole
FAILED test_environment_variable_disables_a_rule
FAILED test_environment_variable_selects_profile_and_option_wins
FAILED test_invalid_rule_id_from_environment_exits_two
FAILED test_malformed_user_file_warns_once_and_is_skipped
FAILED test_project_file_beats_user_file_and_user_file_beats_system_file
FAILED test_unknown_key_in_project_file_is_ignored
11 failed, 3 passed, 42 deselected in 2.89s
```

The 3 passing tests assert behavior that already holds (legacy file warning, `--config` replacement, user-over-project list).

## Green phase
Commands and output:

```text
$ python -m pytest -q
1170 passed, 5 skipped, 181 subtests passed in 12.04s

$ PYTHONPATH=src python -m pytest -m slow --timeout=120 -q tests/tools/test_lint_markdown.py tests/test_console_scripts.py tests/test_markdown_lint.py tests/test_markdown_plugins.py
22 passed in 4.66s

$ python -m ruff check src tests
All checks passed!
```

Without `PYTHONPATH=src`, the slow `test_package_root_does_not_load_cli_tool_module` fails with
`ModuleNotFoundError: No module named 'support_python'`: the shared venv has no install of this worktree. It is an environment issue, not a regression.

## Final run after docs and the alias unit test
```text
$ python -m pytest -q
1171 passed, 5 skipped, 181 subtests passed in 11.91s

$ python -m ruff check src tests
All checks passed!

$ lint-markdown check --offline docs CHANGELOG.md
All 25 markdown files passed linting.
```
