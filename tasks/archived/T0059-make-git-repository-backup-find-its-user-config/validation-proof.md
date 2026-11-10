## Walkthrough & Validation

### Red phase
`.venv/Scripts/python -m pytest -q tests/tools/test_git_repository_backup.py`, before the implementation (exit 1):
```text
E       **[ERROR]** Finished git-repository-backup list in 0.0s with status: failed
FAILED tests/tools/test_git_repository_backup.py::TestHarnessCli::test_startup_banner_names_default_config_file
FAILED tests/tools/test_git_repository_backup.py::TestConfig::test_config_resolution_new_old_legacy_and_absent
FAILED tests/tools/test_git_repository_backup.py::TestConfig::test_default_config_path_follows_user_config_path
FAILED tests/tools/test_git_repository_backup.py::TestConfig::test_describe_config_marks_each_location
FAILED tests/tools/test_git_repository_backup.py::TestRestoreIntegration::test_installed_cli_legacy_config_and_json_list
FAILED tests/tools/test_git_repository_backup.py::TestRestoreIntegration::test_installed_cli_reads_xdg_config_home_config
6 failed, 102 passed, 50 subtests passed in 45.72s
```

### Green phase
`.venv/Scripts/python -m pytest -q` (exit 0):
```text
1119 passed, 3 skipped, 189 subtests passed in 128.65s (0:02:08)
```
An intermediate full run showed 3 failures in `tests/tools/test_agent_digest.py`, caused by another session's uncommitted edits.
They passed with this task's files stashed, and pass after that session committed `4fd9e11`.

`.venv/Scripts/ruff check .` and `.venv/Scripts/ruff format --check .` (exit 0).

### Integration
Installed `git-repository-backup list --verbose` with `XDG_CONFIG_HOME={{tmp}}/xdg` holding the config (exit 0):
```text
- Config file: {{tmp}}\xdg\git-repository-backup\config.json (default)
alpha  {{tmp}}\root\alpha
```
Installed `git-repository-backup list` with only the old `~/.config` file (exit 0), stderr:
```text
**[WARN]**  Reading config {{tmp}}\home\.config\git-repository-backup\config.json from its old location; move it to {{tmp}}\xdg\git-repository-backup\config.json. The old location is dropped in v3.0.0.
```
`test_installed_cli_reads_xdg_config_home_config` automates the first scenario.
