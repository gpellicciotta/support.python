# Validation Proof

Verification evidence for `T0020` confirming generalized `agent-digest` CLI behavior, front-matter ordering, link rewriting, merged `check` validations, and `dev-guidelines` parity.

---

## TDD Red Phase
Running `python -m pytest tests/tools/test_agent_digest.py -q` before implementing generalized `<PATH>...` collection and folded `check` failed as expected:
```text
FFFFFFFFFFFFFFFFFFF..FFFFF.F                                             [100%]
=========================== short test summary info ===========================
FAILED tests/tools/test_agent_digest.py::TestAgentDigestConstantsRemoval::test_dev_guidelines_specific_constants_are_removed
FAILED tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_collect_paths_orders_by_index_then_cli_discovery_order
FAILED tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_non_integer_index_exits_1_and_names_file
FAILED tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_missing_path_exits_2
FAILED tests/tools/test_agent_digest.py::TestPathCollectionAndOrdering::test_non_md_file_argument_exits_2
FAILED tests/tools/test_agent_digest.py::TestSkillLinkAndOriginDerivation::test_any_skills_skill_md_link_rewrites_to_the_name_skill
FAILED tests/tools/test_agent_digest.py::TestSkillLinkAndOriginDerivation::test_link_base_derived_from_git_origin_and_branch
FAILED tests/tools/test_agent_digest.py::TestSkillLinkAndOriginDerivation::test_no_git_remote_leaves_repo_links_relative
FAILED tests/tools/test_agent_digest.py::TestMergedCheckValidation::test_check_folds_all_validation_rules_and_skill_index
FAILED tests/tools/test_agent_digest.py::TestGenerateAgentDigestCli::test_validate_is_rejected_as_unknown_subcommand_exiting_2
25 failed, 3 passed, 4 subtests passed in 4.30s
```

---

## Unit, CLI, and Console Script Suite
Running `python -m pytest tests/tools/test_agent_digest.py tests/tools/test_agent_files.py tests/test_console_scripts.py -q` after implementation:
```text
................................................................................................................... [ 84%]
.....................                                                    [100%]
136 passed, 29 subtests passed in 26.00s
```

Running `python -m ruff check src/ tests/` and `python -m ruff format --check src/ tests/`:
```text
All checks passed!
105 files already formatted
```

Running `python -m support_python.tools.lint_markdown check docs --offline`:
```text
Starting lint-markdown v2.0.14-pre+2e7ca39 with configuration:
- Command: check
- Log file: none
- Log level: INFO
- Verbose: false
All 10 markdown files passed linting.
Finished lint-markdown check in 0.3s with status: succeeded
```

---

## Integration Check on `dev-guidelines`
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
