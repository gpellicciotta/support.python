## Walkthrough & Validation

### Key Changes
- Removed `get_digest_generator` and `ensure_digest`; `sync` and `check` only read the existing digest.
- Defaulted the digest to `agent-digest.md` and skills to `agent-skills` under the project root or config directory.
- A missing or empty digest exits 1 with an `agent-digest generate <PATH>...` hint.
- **[Decided]** Kept the legacy `MARKER_BEGIN` text so already-installed guarded blocks still match.

### Red Phase (tests before implementation)
Command: `.venv/Scripts/python -m pytest -q tests/tools/test_agent_files.py` (exit 1).
`HiddenTargetFileTests` and the JSON check test also failed, because the unpatched generator rewrote their digests.
```text
FAILED tests/tools/test_agent_files.py::HarnessErrorFormattingTests::test_missing_digest_logs_indicator_error_and_exits_one
FAILED tests/tools/test_agent_files.py::NoDigestGenerationTests::test_module_exposes_no_digest_generator_hooks
FAILED tests/tools/test_agent_files.py::NoDigestGenerationTests::test_sync_and_check_never_import_agent_digest_or_rewrite_digest
FAILED tests/tools/test_agent_files.py::HiddenTargetFileTests::test_main_update_succeeds_with_hidden_agent_skill_and_manifest_files
FAILED tests/tools/test_agent_files.py::RepoRootResolutionTests::test_check_and_sync_repo_root_install_existing_digest_from_unrelated_cwd
FAILED tests/tools/test_agent_files.py::RepoRootResolutionTests::test_resolves_default_digest_and_skills_dir_under_repo_root_from_working_directory
FAILED tests/tools/test_agent_files.py::SupportPythonAgentFilesCliTests::test_check_json_output_parses_and_reports_pending_and_up_to_date
FAILED tests/tools/test_agent_files.py::AgentFilesConfigTests::test_default_paths_resolve_against_config_directory_when_config_sets_no_paths
FAILED tests/tools/test_agent_files.py::AgentFilesConfigTests::test_load_config_defaults_when_no_file_present
FAILED tests/tools/test_agent_files.py::AgentFilesConfigTests::test_load_config_overrides_from_json_and_cli_flags
FAILED tests/tools/test_agent_files.py::SecondProjectMarkerAndManifestTests::test_second_fixture_project_syncs_without_touching_dev_guidelines
FAILED tests/tools/test_agent_files.py::ToolRegistryAndAddedToolTests::test_added_registry_entry_is_listed_and_synced_like_builtin_tools
FAILED tests/tools/test_agent_files.py::ToolRegistryAndAddedToolTests::test_installed_agent_files_sync_and_check_integration
13 failed, 87 passed, 14 subtests passed in 3.87s
```

### Green Phase
Command: `.venv/Scripts/python -m pytest -q tests/tools/test_agent_files.py` (exit 0).
```text
100 passed, 14 subtests passed in 3.72s
```

Command: `.venv/Scripts/python -m pytest -q` (exit 0).
```text
749 passed, 3 skipped, 81 subtests passed in 82.87s (0:01:22)
```

Commands: `.venv/Scripts/ruff check .` and `.venv/Scripts/ruff format --check .` (both exit 0).
```text
All checks passed!
129 files already formatted
```

Command: `.venv/Scripts/lint-markdown check docs/tools/agent-files.md` (exit 0).
Remaining `README.md` and `CHANGELOG.md` issues sit on untouched lines and predate this task.
```text
Finished lint-markdown check in 0.0s with status: succeeded
```

### Integration Scenario (installed console scripts)
A temporary project held `notes/sample-rules.md`, a `notes/sample-skill.md` skill source, and `.agent-files.json`.
The config routed a `claude-code` tool to a temporary `targets/` directory.
```text
$ agent-files check   # before generate
**[ERROR]** <agent-files> digest not found or empty at {{tmp}}\proj\agent-digest.md; create it with 'agent-digest generate <PATH>... --digest {{tmp}}\proj\agent-digest.md --skills-dir {{tmp}}\proj\agent-skills'
**[ERROR]** Finished agent-files check in 0.0s with status: failed
exit=1
$ agent-digest generate notes --digest agent-digest.md --skills-dir agent-skills
exit=0
$ agent-files check
exit=1
$ agent-files sync
<claude-code> sync: guarded dev-guidelines block synced
<claude-code> sync: synced skill 'sample-skill'
Finished agent-files sync in 0.0s with status: succeeded
exit=0
$ agent-files check
Finished agent-files check in 0.0s with status: succeeded
exit=0
```
The same scenario runs automatically in `test_installed_agent_files_sync_and_check_integration`.
