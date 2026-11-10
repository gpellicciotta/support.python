# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0091 Make DevopsCli help summaries and examples come from the project adapter, so GradleProject help describes Gradle tasks.
- [x] T0089 Replace the stale update-global-agent-files.py text in the agent-files guarded block marker, still recognizing existing blocks.
- [ ] T0088 Make lint-markdown resolve GitHub links to sibling checkouts only for configured owners, defaulting to none.
- [ ] T0087 Default APP_AUTHOR and COPYRIGHT to empty, omitting the banner copyright when empty, while the bundled tools keep theirs.
- [ ] T0086 [needs: T0084] Add constructor parameters for the support.java flags, commands, endpoints, and env-file names in the devops service managers.
- [ ] T0084 [needs: T0083] Remove the auth and counters schema transformers and the app parameter from the SQL anonymizer, requiring a transformers map.
- [ ] T0083 Add a declarative column-rule transformer builder and public SQL value helpers to the SQL anonymizer.
- [ ] T0065 [protocol: adhoc] Make every tool's --version report the installed support-python version instead of the current directory's project version.
- [ ] T0066 [protocol: adhoc] Make agent-files sync --dry-run --no-prune report kept stale skills instead of removals.
- [ ] T0067 [protocol: adhoc] Retry lint-markdown external link checks with GET when HEAD returns 404, as webawesome.com does.
- [ ] T0068 Move git-repository-backup settings onto the shared resolver, adding environment variables, a system file, and the config group.
- [ ] T0069 Move lint-markdown settings onto the shared resolver, adding user and system files, environment variables, and the config group.
- [ ] T0070 Move agent-files settings onto the shared resolver, adding user and system files, environment variables, and the config group.
- [ ] T0071 Split the test suite into a parallel fast default suite and a marked slow suite, with per-test timeouts.
- [ ] T0072 Let DevopsCli run the slow test suite through test --slow, and run both suites in check and release.
- [ ] T0073 Fail the test run when a test writes into the real home directory or the repository's own .plan directory.
- [ ] T0074 Add --format text|json to processes kill, reporting each killed, skipped, and failed PID.
- [ ] T0075 [needs: T0070] Add --format text|json to agent-files sync, reporting each tool's planned and applied changes.
- [ ] T0076 [needs: T0069] Add --format text|json to lint-markdown fix, reporting fixed files and remaining issues.
- [ ] T0077 Add --format text|json to agent-digest generate, reporting written and unchanged digest and skill files.
- [ ] T0078 [needs: T0068] Add --format text|json to git-repository-backup backup and restore, reporting per-repository results.
- [ ] T0079 Show every action's options in ToolHarness help --verbose, with metavars and consistent help text.
- [ ] T0080 Document every public symbol in src/ and enforce public docstrings with ruff pydocstyle rules.
- [ ] T0081 [needs: T0068, T0069, T0070, T0074, T0075, T0076, T0077, T0078] Specify the configuration file formats and JSON output documents of all five tools under docs/specs/.
- [ ] T0090 [needs: T0085] Make decrypt_property_value fail clearly when the cryptography package is missing instead of returning the ciphertext.
- [ ] T0085 [needs: T0084] Require an explicit salt and AES key in the crypto helpers, removing STANDARD_SALT and DEFAULT_AES_KEY_HEX.
- [ ] T0082 Add a typed confirmation with --yes to processes kill, or document why it is exempt from that CLI rule.

---

## Backlog
- [-] T0093 [reason: ReleasePipeline accepts frozen versions for resumed releases; release tasks such as doFullRelease own the -pre precondition.] Make GradleProject.release refuse a version without -pre before the confirmation, as ReleasePipeline does.
- [ ] T0092 Let project adapters supply the DevopsCli exit-code text, dropping the virtual environment wording for Gradle and npm projects.
- [~] T0046 [owner: @claude-code] Migrate pinned sibling consumers (auth, counters.server, todos.server, template.python) off build_action_parser, print_help, and print_version when they upgrade to support-python v2
