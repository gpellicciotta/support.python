# Validation proof T0068

## Red phase
Command:
```text
PYTHONPATH=src python -m pytest tests/tools/test_git_repository_backup.py tests/tools/test_config_keys.py -k "TestSharedSettings or SnakeCase or backup_example" -q --no-header -p no:cacheprovider
```
Result: 16 failed. The `TestSharedSettings` tests fail in `setUp` because `git_repository_backup` has no `system_config_path`:
```text
AttributeError: <module 'support_python.tools.git_repository_backup' ...> does not have the attribute 'system_config_path'
```
`SnakeCaseConfigKeyTests` and the documented-example test fail because `build_schema` does not exist yet.
Note: the red failures share one cause per class, so they prove the missing API, not each behavior.

## Green phase
Fast suite (`PYTHONPATH=src python -m pytest -q -m "not slow"`):
```text
1156 passed, 5 skipped, 181 subtests passed in 11.86s
```
One earlier run showed `tests/test_processes.py::test_child_process_lifecycle_integration` failing once; it passed on the immediate rerun and the full suite (unrelated timing flake, not touched by this task).

Slow backup tests (`python -m pytest tests/tools/test_git_repository_backup.py tests/test_config_actions.py -m slow --timeout=120`):
```text
58 passed, 26 subtests passed in 15.93s
```
Lint: `ruff check src tests` reported `All checks passed!`; `ruff format --check` reported `130 files already formatted`.
`lint-markdown check --offline` reports only the 7 pre-existing issues in the frozen `tests/fixtures/agent_digest/` snapshot.
Updated tests: `test_invalid_config_json_warns_and_is_ignored`, `test_non_string_keyring_config_warns_and_is_ignored`, and `test_non_string_config_values_warn_and_are_ignored` replace the old exit-2 tests, per the task goal.
