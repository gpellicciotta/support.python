# Project Planning
An overview of all tasks and their planning.

---

## Next Milestone
- [x] T0019 Port the dev-guidelines agent digest generator unchanged into support_python.tools.agent_digest with an agent-digest console script.
- [x] T0020 Generalize agent-digest to take Markdown paths, order files by front-matter index, and fold validation into check.
- [-] T0021 [reason: Superseded by T0024, which installs lint-markdown as a console script within the v2.0.0 tool restructuring.] Expose the Markdown linter as an installable lint-markdown console script.
- [-] T0022 [reason: Superseded by T0024 and T0029, which install agent-files and align its verbs and tool name.] Expose the agent-files sync as an installable agent-files console script.
- [x] T0023 Record ADR-0003 on tool, library, and script boundaries with shared CLI conventions, and open v2.0.0-pre.
- [x] T0024 Replace the support-python command with lint-markdown, agent-files, and git-repository-backup console scripts, and drop the wrapper scripts.
- [x] T0025 Move the processes, agent-files, and backup CLI modules into the support_python.tools package without behavior changes.
- [x] T0026 Split the Markdown linter into a support_python.markdown.lint engine and a support_python.tools.lint_markdown CLI module.
- [x] T0027 Rename backup-git-repos to git-repository-backup, read its legacy config with a warning, and add JSON list output.
- [x] T0028 Make ToolHarness configure UTF-8 output for every tool, and remove the ToolLogger and TeeLogger logger aliases.
- [x] T0029 Align agent-files with ADR-0003: canonical sync and check verbs, JSON list output, and .agent-files.json with legacy fallback.
- [x] T0030 Align lint-markdown with ADR-0003: drop the --fix flag, add JSON check output, and rename its config to .lint-markdown.json.
- [x] T0031 Align processes with ADR-0003: add kill --dry-run and rename the table output format to text.
- [x] T0032 Make agent-files consume an existing digest and skills directory instead of regenerating the digest itself.
- [x] T0033 Let lint-markdown load extra rules from plugin modules and list all active rules with a rules action.
- [x] T0034 Convert support_python.devops into a package with steps and services modules, keeping its public imports unchanged.
- [x] T0035 Add support_python.devops.release helpers for version files, CHANGELOG freezing and reopening, release notes, and GitHub origins.
- [x] T0036 Add a dry-runnable ReleasePipeline that freezes, tags, pushes, publishes a GitHub release with assets, and reopens development.
- [x] T0037 Rebuild extract-release-notes, migrate-namespace, and reset-history on support_python.devops.release, and delete scripts/_repo_common.py.
- [x] T0038 Add DevopsCli and PythonProject to support_python.devops, and rebuild this repository's scripts/devops.py on them.
- [x] T0039 Add a GradleProject adapter to support_python.devops for gradlew-based lint, test, build, check, clean, and release.
- [x] T0040 Add a NodeProject adapter to support_python.devops for npm-based lint, format, test, build, check, clean, and release.
- [ ] T0041 Add a deploy action to DevopsCli with shared preconditions, typed confirmation, project deploy steps, and post-deploy verification.
- [ ] T0042 [needs: T0041] Add opt-in docker, db, server, mail, and client action groups to DevopsCli, backed by the devops service managers.
- [ ] T0043 [needs: T0042, T0044] Write the v2.0.0 migration guide, refresh CLAUDE.md, and record migration backlog tasks in consumer repositories.
- [ ] T0044 Rebuild the capture view CLI on ToolHarness, and remove build_action_parser, print_help, print_version, and format_version.

---

## Backlog
*(Currently no tasks)*
