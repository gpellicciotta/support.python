# Validation Proof

Verification evidence for `T0020` confirming generalized `agent-digest` CLI behavior, front-matter ordering, link rewriting, merged `check` validations, and `dev-guidelines` parity.

---

## TDD Red Phase Against Base Module (`2e7ca39`)
Running the delivered [test_agent_digest.py](../../../../tests/tools/test_agent_digest.py) suite against the pre-change `agent_digest.py` at base commit `2e7ca39` (`python -m pytest -o pythonpath={{primary-checkout}}/src tests/tools/test_agent_digest.py -q --tb=no`) fails on all 26 new assertions and subtests (earlier proof listed draft identifiers before test consolidation):
```text
.FF.F..FFFFFFF..FFF..F.F..                                [100%]
=========================== short test summary info ===========================
SUBFAILED(attr='SOURCE_FILES') tests/tools/test_agent_digest.py::TestAgentDigestConstantsRemoval::test_dev_guidelines_specific_constants_are_removed
SUBFAILED(attr='GUIDELINES_DIR') tests/tools/test_agent_digest.py::TestAgentDigestConstantsRemoval::test_dev_guidelines_specific_constants_are_removed
SUBFAILED(attr='DIGEST_PATH') tests/tools/test_agent_digest.py::TestAgentDigestConstantsRemoval::test_dev_guidelines_specific_constants_are_removed
SUBFAILED(attr='SKILLS_DIR') tests/tools/test_agent_digest.py::TestAgentDigestConstantsRemoval::test_dev_guidelines_specific_constants_are_removed
SUBFAILED(attr='PLAN_OWNED_SKILLS') tests/tools/test_agent_digest.py::TestAgentDigestConstantsRemoval::test_dev_guidelines_specific_constants_are_removed
FAILED tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_collect_input_files_excludes_digest_and_skills_dir_inside_input_dir
FAILED tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_collect_input_files_handles_files_recursive_dirs_hidden_dirs_and_duplicates
SUBFAILED(action='generate') tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_generate_and_check_without_paths_report_usage_error_and_exit_2
SUBFAILED(action='check') tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_generate_and_check_without_paths_report_usage_error_and_exit_2
FAILED tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_index_ordering_orders_indexed_then_unindexed_with_stable_ties
SUBFAILED(action='generate') tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_non_integer_index_exits_1_and_names_file
SUBFAILED(action='check') tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_non_integer_index_exits_1_and_names_file
FAILED tests/tools/test_agent_digest.py::TestOutputOptionsAndDefaults::test_generate_respects_custom_digest_and_skills_dir_options
FAILED tests/tools/test_agent_digest.py::TestOutputOptionsAndDefaults::test_generate_uses_default_digest_and_skills_dir_in_cwd
FAILED tests/tools/test_agent_digest.py::TestLinkBaseAndSkillLinks::test_derive_link_base_from_origin_remote_and_branch
FAILED tests/tools/test_agent_digest.py::TestLinkBaseAndSkillLinks::test_github_and_relative_skill_md_urls_rewrite_to_skill_reference
FAILED tests/tools/test_agent_digest.py::TestLinkBaseAndSkillLinks::test_link_base_override_and_missing_origin_keeps_relative_links
FAILED tests/tools/test_agent_digest.py::TestMergedCheckAction::test_check_fails_on_stale_digest_stale_skill_budget_violation_and_unlinked_skill
FAILED tests/tools/test_agent_digest.py::TestMergedCheckAction::test_check_rejects_unknown_frontmatter_keys_and_orphan_reference_files
SUBFAILED(action='generate') tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_action_specific_help_shows_only_target_action
SUBFAILED(action='check') tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_action_specific_help_shows_only_target_action
FAILED tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_check_emits_startup_and_completion_banners_and_logs_to_file
FAILED tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_check_lists_each_up_to_date_skill_only_when_verbose
FAILED tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_help_lists_version_header_actions_options_and_exit_codes
FAILED tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_log_level_error_suppresses_info_output_and_debug_emits_debug
FAILED tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_validate_is_rejected_as_unknown_subcommand_exiting_2
26 failed, 11 passed, 4 subtests passed in 3.19s
```

---

## Green Phase, Linting, and Markdown Validation
Running `python -m pytest tests/tools/test_agent_digest.py -q`, `ruff`, and `lint-markdown check docs --offline`:
```text
Starting lint-markdown v2.0.14-pre+5be8119 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
All 1 markdown files passed linting.
Finished lint-markdown check in 0.1s with status: succeeded
All checks passed!
105 files already formatted
..........................                                [100%]
26 passed, 15 subtests passed in 8.10s
```

---

## Integration Verification on `dev-guidelines`
Running `agent-digest generate guidelines --digest guidelines/agent-digest.md --skills-dir skills` on a clean `dev-guidelines` clone followed by `git status --short` (empty output, zero diff):
```text
Starting agent-digest v2.0.14-pre+5be8119 with configuration:
- Command: generate
- Log file: none
- Log level: INFO
- Verbose: false
- Digest: guidelines/agent-digest.md
- Skills dir: skills
- Max words: 20
- Max bytes: 20480
Generated skills/change-management-guidelines/SKILL.md (71 lines).
Generated skills/cli-guidelines/SKILL.md (34 lines).
Generated skills/database-guidelines/SKILL.md (22 lines).
Generated skills/java-guidelines/SKILL.md (48 lines).
Generated skills/javascript-guidelines/SKILL.md (32 lines).
Generated skills/logging-guidelines/SKILL.md (55 lines).
Generated skills/markdown-guidelines/SKILL.md (56 lines).
Generated skills/process-management-guidelines/SKILL.md (34 lines).
Generated skills/project-setup-guidelines/SKILL.md (57 lines).
Generated skills/python-guidelines/SKILL.md (48 lines).
Generated skills/testing-guidelines/SKILL.md (66 lines).
Generated skills/ui-guidelines/SKILL.md (89 lines).
Generated guidelines/agent-digest.md (92 lines, 6281 bytes).
Finished agent-digest generate in 0.7s with status: succeeded
```

Running `agent-digest check guidelines --digest guidelines/agent-digest.md --skills-dir skills --skill-index guidelines/general-guidelines.md` against `dev-guidelines`:
```text
Starting agent-digest v2.0.14-pre+2e7ca39 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
- Digest: guidelines/agent-digest.md
- Skills dir: skills
- Max words: 20
- Max bytes: 20480
All 12 derived skill(s) are up to date.
guidelines/agent-digest.md is up to date and within budget (6281 bytes).
All directive sentences satisfy the 20-word budget and digest size is within 20480 bytes (6281 bytes).
Finished agent-digest check in 0.7s with status: succeeded
```
