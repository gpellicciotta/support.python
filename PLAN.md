# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0104 Add skills-only installation to agent-files, as a command mode and an importable function, matching plan's current skill installer.
- [x] T0105 Rewrite GitHub links ending in docs/guidelines/{{name}}.md to the skill reference, as links ending in skills/{{name}}/SKILL.md are today.
- [x] T0106 Fix flaky test_child_process_lifecycle_integration, which failed once in the fast suite under xdist load.
- [x] T0073 Fail the test run when a test writes into the real home directory or the repository's own .plan directory.
- [x] T0065 [owner: @gemini, session: antigravity-20261110-51d0ec] [protocol: adhoc] Make every tool's --version report the installed support-python version instead of the current directory's project version.
- [x] T0066 [owner: @gemini, session: antigravity-20261110-14256a] [protocol: adhoc] Make agent-files sync --dry-run --no-prune report kept stale skills instead of removals.
- [x] T0067 [owner: @gemini, session: antigravity-20261110-8d3a12] [protocol: adhoc] Retry lint-markdown external link checks with GET when HEAD returns 404, as webawesome.com does.
- [x] T0098 Make ToolHarness version output show the -pre suffix instead of the PEP 440 rc0 form from package metadata.
- [x] T0097 Derive version build metadata from the support.python checkout, not an enclosing repository.
- [x] T0087 Default APP_AUTHOR and COPYRIGHT to empty, omitting the banner copyright when empty, while the bundled tools keep theirs.
- [x] T0088 Make lint-markdown resolve GitHub links to sibling checkouts only for configured owners, defaulting to none.
- [x] T0071 Split the test suite into a parallel fast default suite and a marked slow suite, with per-test timeouts.
- [x] T0072 Let DevopsCli run the slow test suite through test --slow, and run both suites in check and release.
- [x] T0083 Add a declarative column-rule transformer builder and public SQL value helpers to the SQL anonymizer.
- [x] T0084 Remove the auth and counters schema transformers and the app parameter from the SQL anonymizer, requiring a transformers map.
- [x] T0085 Require an explicit salt and AES key in the crypto helpers, removing STANDARD_SALT and DEFAULT_AES_KEY_HEX.
- [x] T0090 Make decrypt_property_value fail clearly when the cryptography package is missing instead of returning the ciphertext.
- [x] T0086 Add constructor parameters for the support.java flags, commands, endpoints, and env-file names in the devops service managers.
- [x] T0079 Show every action's options in ToolHarness help --verbose, with metavars and consistent help text.
- [x] T0082 Add a typed confirmation with --yes to processes kill, or document why it is exempt from that CLI rule.
- [x] T0074 Add --format text|json to processes kill, reporting each killed, skipped, and failed PID.
- [x] T0077 Add --format text|json to agent-digest generate, reporting written and unchanged digest and skill files.
- [x] T0068 Move git-repository-backup settings onto the shared resolver, adding environment variables, a system file, and the config group.
- [x] T0069 Move lint-markdown settings onto the shared resolver, adding user and system files, environment variables, and the config group.
- [x] T0070 Move agent-files settings onto the shared resolver, adding user and system files, environment variables, and the config group.
- [x] T0075 Add --format text|json to agent-files sync, reporting each tool's planned and applied changes.
- [x] T0076 Add --format text|json to lint-markdown fix, reporting fixed files and remaining issues.
- [x] T0078 Add --format text|json to git-repository-backup backup and restore, reporting per-repository results.
- [x] T0081 Specify the configuration file formats and JSON output documents of all five tools under docs/specs/.
- [x] T0080 Document every public symbol in src/ and enforce public docstrings with ruff pydocstyle rules.
- [x] T0103 [owner: @claude, session: claude-20261111-011c8e] [protocol: adhoc] Release all changes with devops release after running its dry run, once every other task is done.

---

## Backlog
*(Currently no tasks)*
