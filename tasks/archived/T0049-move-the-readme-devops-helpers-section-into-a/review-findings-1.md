---
task: T0049
round: 1
verdict: rejected
reviewer: "@claude-reviewer"
reviewed_at: 2026-11-10T07:31:01Z
reviewed_commit: "70afcd5"
base_commit: "70afcd5"
---
# T0049 Review Findings, Round 1

Verdict: reject.
Two statements from the original README DevOps section are missing from the tutorial.
The technical spec requires that the tutorial keep every README statement.

## Checks
- Completion check: `.venv/Scripts/lint-markdown check --offline README.md docs/index.md docs/migration-v2.md docs/tutorials` passed with exit code 0.
- Version: `pyproject.toml` `2.0.31-pre` matches the top `CHANGELOG.md` heading `## v2.0.31-pre`.
- Task file: `plan tasks validate` passed.
- Links: all eight relative links in `docs/tutorials/devops-scripts.md` resolve.
  The README, `docs/index.md`, and `docs/migration-v2.md` links to the tutorial also resolve.
- Stale anchors: no `.md` or `.py` file outside `.venv` and `.plan` still links to `#devops-script-helpers-and-environment-managers`.
- Exports: every devops symbol in the tutorial is importable from `support_python.devops`.
  The step runners and service managers are also exported from `support_python`.
- Moving the `runner`/`add_action` sentence under `DevopsCli` is accurate, because every `Project` subclass takes `runner`.

## Findings

### F1 (defect): `help` and `version` actions dropped
- Location: `docs/tutorials/devops-scripts.md:122-126`.
- Original: "Its actions are `lint`, `format`, `test`, `build`, `check`, `clean`, `versions`, and `release`, plus `help` and `version`."
- The tutorial's action list leaves out `help` and `version`.
- Fix: add a bullet after line 126: "- `help` and `version`, from `ToolHarness`."

### F2 (defect): release asset sentence dropped
- Location: `docs/tutorials/devops-scripts.md:126`.
- Original: "It attaches the outputs of that post-freeze build, never the `-pre` build from `check`."
- This sentence does not appear anywhere in the tutorial.
- Fix: extend the `release` bullet with "It attaches the outputs of that post-freeze build, never the `-pre` build from `check`."

### F3 (nit): "Every symbol below" overclaims
- Location: `docs/tutorials/devops-scripts.md:13`.
- The tutorial also names `CliLogger` and `ToolHarness`, and `support_python.devops` exports neither one.
- Fix: write "Every devops symbol below is importable from `support_python.devops`".

### F4 (nit): Docker fallback attributed to the resolver
- Location: `docs/tutorials/devops-scripts.md:19`.
- `resolve_cloud_sql_proxy_bin` only returns a path or `None`.
- Only `CloudSqlProxyManager.start` falls back to Docker, and only it fails cleanly when Docker is missing.
- Fix: "`resolve_cloud_sql_proxy_bin` searches `PATH`, `repo_root`, and user or Cloud SDK `bin` directories.
  `CloudSqlProxyManager` uses it and falls back to Docker, failing cleanly when Docker is missing."
