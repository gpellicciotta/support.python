# Validation Proof

## Red phase
Command: `python -m pytest tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests tests/test_config.py -k "SharedSettings or normalize_hook" -q --no-header`
```
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_config_list_names_every_setting_with_sources
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_config_runs_even_when_a_tool_entry_is_invalid
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_config_set_user_file_and_reject_bad_values
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_config_targets_the_project_file_by_default
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_environment_variable_beats_project_file_and_loses_to_option
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_environment_variables_set_lists_and_booleans
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_invalid_value_warns_and_falls_to_the_next_source
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_malformed_user_file_warns_once_and_is_skipped
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_project_file_beats_user_file_and_user_file_beats_system_file
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_relative_repo_root_resolves_against_the_file_that_sets_it
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_replace_tools_drops_the_defaults
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_tools_merge_across_sources_by_tool_name
FAILED tests/tools/test_agent_files.py::AgentFilesSharedSettingsTests::test_unknown_key_is_ignored_and_listed_with_debug
FAILED tests/test_config.py::ResolveSettingsTests::test_normalize_hook_converts_file_values_before_parsing
14 failed, 2 passed, 16 deselected in 1.64s
```

## Green phase: fast suite
Command: `python -m pytest -q --no-header`
```
....................................................uuuu................ [ 73%]
...............uu.uu..uu..uu.u.......................u.uu..........uu... [ 78%]
.................u...u..u.uuu.u.u....................................... [ 83%]
.......u...u..u...u.........uuuu.............................u.......... [ 89%]
...........u.....uu.....................uuu..uuuuuu.u.uu.....u...u...... [ 93%]
.........................................................u..u........... [ 99%]
....                                                                     [100%]
1186 passed, 5 skipped, 181 subtests passed in 12.60s
```

## Affected slow tests
Command: `python -m pytest -m slow --timeout=120 -q --no-header tests/tools/test_agent_files.py tests/test_config.py tests/tools/test_config_keys.py`
```
bringing up nodes...
bringing up nodes...

...                                                                      [100%]
3 passed in 4.08s
```
