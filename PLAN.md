# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0073 Fail the test run when a test writes into the real home directory or the repository's own .plan directory.
- [x] T0065 [owner: @gemini, session: antigravity-20261110-51d0ec] [protocol: adhoc] Make every tool's --version report the installed support-python version instead of the current directory's project version.
- [ ] T0066 [protocol: adhoc] Make agent-files sync --dry-run --no-prune report kept stale skills instead of removals.
- [ ] T0067 [protocol: adhoc] Retry lint-markdown external link checks with GET when HEAD returns 404, as webawesome.com does.
- [ ] T0098 Make ToolHarness version output show the -pre suffix instead of the PEP 440 rc0 form from package metadata.
- [ ] T0097 Derive version build metadata from the support.python checkout, not an enclosing repository.
- [ ] T0087 Default APP_AUTHOR and COPYRIGHT to empty, omitting the banner copyright when empty, while the bundled tools keep theirs.
- [ ] T0088 Make lint-markdown resolve GitHub links to sibling checkouts only for configured owners, defaulting to none.
- [ ] T0071 Split the test suite into a parallel fast default suite and a marked slow suite, with per-test timeouts.
- [ ] T0072 Let DevopsCli run the slow test suite through test --slow, and run both suites in check and release.
- [ ] T0083 Add a declarative column-rule transformer builder and public SQL value helpers to the SQL anonymizer.
- [ ] T0084 [needs: T0083] Remove the auth and counters schema transformers and the app parameter from the SQL anonymizer, requiring a transformers map.
- [ ] T0085 [needs: T0084] Require an explicit salt and AES key in the crypto helpers, removing STANDARD_SALT and DEFAULT_AES_KEY_HEX.
- [ ] T0090 [needs: T0085] Make decrypt_property_value fail clearly when the cryptography package is missing instead of returning the ciphertext.
- [ ] T0086 [needs: T0084] Add constructor parameters for the support.java flags, commands, endpoints, and env-file names in the devops service managers.
- [ ] T0079 Show every action's options in ToolHarness help --verbose, with metavars and consistent help text.
- [ ] T0082 Add a typed confirmation with --yes to processes kill, or document why it is exempt from that CLI rule.
- [ ] T0074 Add --format text|json to processes kill, reporting each killed, skipped, and failed PID.
- [ ] T0077 Add --format text|json to agent-digest generate, reporting written and unchanged digest and skill files.
- [ ] T0068 Move git-repository-backup settings onto the shared resolver, adding environment variables, a system file, and the config group.
- [ ] T0069 Move lint-markdown settings onto the shared resolver, adding user and system files, environment variables, and the config group.
- [ ] T0070 Move agent-files settings onto the shared resolver, adding user and system files, environment variables, and the config group.
- [ ] T0075 [needs: T0070] Add --format text|json to agent-files sync, reporting each tool's planned and applied changes.
- [ ] T0076 [needs: T0069] Add --format text|json to lint-markdown fix, reporting fixed files and remaining issues.
- [ ] T0078 [needs: T0068] Add --format text|json to git-repository-backup backup and restore, reporting per-repository results.
- [ ] T0081 [needs: T0068, T0069, T0070, T0074, T0075, T0076, T0077, T0078] Specify the configuration file formats and JSON output documents of all five tools under docs/specs/.
- [ ] T0080 Document every public symbol in src/ and enforce public docstrings with ruff pydocstyle rules.
- [ ] T0103 [protocol: adhoc] [needs: T0066, T0067, T0098, T0097, T0087, T0088, T0071, T0072, T0083, T0084, T0085, T0090, T0086, T0079, T0082, T0074, T0077, T0068, T0069, T0070, T0075, T0076, T0078, T0081, T0080] Release all changes with devops release after running its dry run, once every other task is done.

---

## Backlog
- [ ] T0104 Add skills-only installation to agent-files, as a command mode and an importable function, matching plan's current skill installer.
