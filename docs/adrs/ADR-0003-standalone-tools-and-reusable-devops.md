# ADR-0003: Standalone Tools and Reusable DevOps

## Status
Accepted.

## Context
`support-python` evolved with two overlapping CLI surfaces and an unfinished devops story:
- Some tools shipped under a multi-command `support-python` entry point (`support-python lint markdown`, `support-python agent-files`, `support-python backup`), while `processes` shipped as its own console script and wrapper scripts remained in `scripts/`.
- Consumers and CI pipelines invoke each utility directly by tool name (`processes`, `agent-files`, `agent-digest`, `lint-markdown`, `git-repository-backup`) rather than through an umbrella `support-python` command.
- CLI flags, verbs, config discovery, and output formats varied across tools instead of following one uniform contract.
- Meanwhile, [ADR-0001-devops-scripts-toolkit-scope.md](ADR-0001-devops-scripts-toolkit-scope.md) kept release pipelines, build adapters, and deploy precondition checks inside each consumer repository's `devops.py` script, causing copy-paste drift across Python, Gradle, and Node projects even where only project adapters and service flags differed.

## Decision
### Deliverables and Entry Points
- The `support-python` distribution provides the `support_python` library and five standalone console scripts:
  - `processes`
  - `agent-files`
  - `agent-digest`
  - `lint-markdown`
  - `git-repository-backup`
- Remove the `support-python` console script and provide no `python -m support_python` entry point.

### Installation
- Users install the five standalone tools per user or globally with `pipx install`, `uv tool install`, `pip install --user`, or `python scripts/install-from-github-release.py {{version}} --global`.
- Inside a repository checkout, the virtual environment's console scripts serve directly.

### Module Layout and Naming
- Each standalone tool's CLI lives in `support_python.tools.{{snake-name}}` and exposes `main(argv) -> int`.
- Reusable domain logic lives in library modules such as `support_python.markdown.lint` and `support_python.processes`.
- A tool module under `support_python.tools` may keep CLI-specific or tool-only logic that no other module needs.
- For every tool, the console script name, `TOOL_NAME`, and banner name are identical.
- Naming across the repository follows a strict mapping:
  - Module: `src/support_python/tools/{{snake-name}}.py`
  - Documentation page: `docs/tools/{{name}}.md`
  - Test module: `tests/tools/test_{{snake-name}}.py`

### Repository Scripts
`scripts/` retains only non-installed scripts:
- [extract-release-notes.py](../../scripts/extract-release-notes.py), `migrate-namespace.py`, and `reset-history.py` build on the `support_python` library and operate on the Git repository of the current working directory.
- [install-from-github-release.py](../../scripts/install-from-github-release.py) remains stdlib-only and self-contained because it installs `support-python` itself.
- [bootstrap-dev-environment.py](../../scripts/bootstrap-dev-environment.py) (stdlib-only, paired with [_cli_common.py](../../scripts/_cli_common.py)) and [devops.py](../../scripts/devops.py) remain internal to this repository.

### Shared CLI Conventions
Every standalone tool follows uniform CLI conventions:
- Build on `support_python.cli.ToolHarness`, inheriting its standard help, version, verbosity, and logging options.
- `ToolHarness` configures UTF-8 console output centrally; individual tools do not call UTF-8 setup helpers themselves.
- Exit codes:
  - `0` for success.
  - `1` for operational failure or findings reported by `check`.
  - `2` for invalid CLI arguments.
- Standard verbs:
  - `list` displays an inventory.
  - `check` runs read-only validation and exits `1` on findings or drift.
  - Domain verbs perform writes (`sync`, `fix`, `generate`, `kill`, `backup`, `restore`).
- Every writing action accepts `--dry-run`, which reports planned changes and writes nothing.
- Every `list` and `check` action accepts `--format text|json` (defaulting to `text`); `json` mode emits a single JSON document on `stdout`.
- Configuration discovery:
  - Project-scoped tools read `./.{{tool-name}}.json` from the project root (`.lint-markdown.json` and `.agent-files.json`).
  - User-scoped tools read `~/.config/{{tool-name}}/config.json` (`git-repository-backup`).
  - `--config {{path}}` overrides automatic discovery on any tool that reads configuration.
  - Legacy configuration paths (`.markdown-lint.json`, `agent-files.json`, and `~/.config/backup-git-repos/config.json`) remain supported with a deprecation warning throughout `v2.x` and are removed in `v3.0.0`.

### Reusable DevOps Package
- Convert `support_python.devops` into a package with submodules:
  - `steps`
  - `services`
  - `release`
  - `projects`
  - `cli`
- `DevopsCli` provides the standard actions `lint`, `format`, `test`, `build`, `check`, `clean`, `versions`, `release`, and `deploy`.
- Built-in project adapters cover standard ecosystems: `PythonProject`, `GradleProject`, and `NodeProject`.
- Opt-in service action groups cover local infrastructure and verification: `docker`, `db`, `server`, `mail`, and `client`.
- Each consuming repository keeps a thin `devops.py` entry script in `scripts/` and pins `support-python` via the `scripts/requirements.txt` mechanism from [ADR-0001-devops-scripts-toolkit-scope.md](ADR-0001-devops-scripts-toolkit-scope.md).
- Do not ship a global `devops` console script, because build and release behavior must remain pinned per project for reproducible CI.

### Relation to ADR-0001 and Versioning
- This decision partially supersedes [ADR-0001-devops-scripts-toolkit-scope.md](ADR-0001-devops-scripts-toolkit-scope.md): the release pipeline, project build adapters (`PythonProject`, `GradleProject`, `NodeProject`), and deploy preconditions and confirmation prompts move into `support_python.devops`.
- Project-specific deploy step bodies, stdlib-only bootstrap scripts, and the per-project `scripts/requirements.txt` pinning mechanism from [ADR-0001-devops-scripts-toolkit-scope.md](ADR-0001-devops-scripts-toolkit-scope.md) remain in force.
- Removing the `support-python` CLI entry point, renaming commands and configuration files, and restructuring `support_python.devops` are backward-incompatible changes; open `v2.0.0-pre` for the next release.

## Alternatives Considered
- Ship a single `support-python` umbrella command with subcommands for every tool. Rejected: users, agent skills, and downstream CI call the standalone tool names directly.
- Ship a global `devops` console script installed alongside the five standalone tools. Rejected: unpinned global `devops` execution breaks per-project build and release reproducibility in CI.
- Centralize project-specific deploy step bodies inside `support_python.devops`. Rejected: deploy steps diverge functionally across services, migrations, and cloud targets, as [ADR-0001-devops-scripts-toolkit-scope.md](ADR-0001-devops-scripts-toolkit-scope.md) established.

## Consequences
- Positive: Five self-contained console scripts share one predictable CLI contract for verbs, exit codes, `--dry-run`, `--format text|json`, and config discovery.
- Positive: Consumer repositories replace hundreds of lines of duplicated `devops.py` release, build, and service wiring with a thin configuration over `DevopsCli`.
- Negative: Breaking CLI and module changes require a major version bump to `v2.0.0` and coordinated updates in downstream repositories and agent skills.
- Negative: Legacy config path fallback and deprecation warnings must be maintained throughout `v2.x` until `v3.0.0`.
