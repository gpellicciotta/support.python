### ADR-0003 Decisions
Write `docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md` with Status, Context, Decision, Alternatives Considered, and Consequences sections, like ADR-0001.

1. **Deliverables.** The `support-python` distribution provides a library and five console scripts:
   `processes`, `agent-files`, `agent-digest`, `lint-markdown`, and `git-repository-backup`.
   There is no `support-python` command and no `python -m support_python` entry point.
2. **Installation.** Users install the tools per user or globally with `pipx install`, `uv tool install`, `pip install --user`,
   or `python scripts/install-from-github-release.py <version> --global`. In a checkout, the venv's console scripts serve.
3. **Layout.** Each tool's CLI lives in `support_python.tools.<snake_name>` and exposes `main(argv) -> int`.
   Reusable logic lives in library modules such as `support_python.markdown.lint` and `support_python.processes`.
   A tool module may keep logic that no other module needs.
4. **Naming.** Console script name, `TOOL_NAME`, and banner name are identical.
   The module is `tools/<snake_name>.py`, the docs page `docs/tools/<name>.md`, and the tests `tests/tools/test_<snake_name>.py`.
5. **Scripts.** `scripts/` keeps only non-installed scripts:
   - `extract-release-notes.py`, `migrate-namespace.py`, and `reset-history.py` build on the library and act on the
     Git repository of the current directory.
   - `install-from-github-release.py` stays stdlib-only and self-contained, because it installs the library.
   - `bootstrap-dev-environment.py` (stdlib-only, with `_cli_common.py`) and `devops.py` are internal to this repository.
6. **CLI conventions for every tool.**
   - Build on `support_python.cli.ToolHarness`, with its standard help, version, verbosity, and logging options.
   - Exit codes: 0 success, 1 operational failure or findings from `check`, 2 invalid arguments.
   - Verbs: `list` shows an inventory, `check` is read-only and exits 1 on findings or drift, and each tool has
     domain verbs that write (`sync`, `fix`, `generate`, `kill`, `backup`, `restore`).
   - Every writing action accepts `--dry-run`, which reports planned changes and writes nothing.
   - Every `list` and `check` accepts `--format text|json`, default `text`; JSON mode prints one JSON document on stdout.
   - `ToolHarness` configures UTF-8 console output; tools do not.
   - Project-scoped tools read `./.<tool-name>.json` from the project root: `.lint-markdown.json` and `.agent-files.json`.
   - User-scoped tools read `~/.config/<tool-name>/config.json`: `git-repository-backup`.
   - `--config PATH` overrides discovery.
   - Legacy config names (`.markdown-lint.json`, `agent-files.json`, `~/.config/backup-git-repos/config.json`) are read
     with a warning throughout v2.x and dropped in v3.0.0.
7. **Reusable devops.** `support_python.devops` becomes a package with `steps`, `services`, `release`, `projects`, and `cli` modules.
   - `DevopsCli` offers the standard actions `lint`, `format`, `test`, `build`, `check`, `clean`, `versions`, `release`, and `deploy`.
   - Project adapters: `PythonProject`, `GradleProject`, and `NodeProject`.
   - Opt-in service action groups: `docker`, `db`, `server`, `mail`, and `client`.
   - A consumer keeps a thin `scripts/devops.py` and pins `support-python` through the ADR-0001 mechanism.
   - There is no global `devops` command, because release behavior must be pinned per project for reproducible CI.
8. **Relation to ADR-0001.** ADR-0003 supersedes "keep deploy scripts project-local" for the release pipeline, the build
   adapters, and the deploy preconditions and confirmation. Deploy steps themselves, bootstrap scripts, and the
   pinning mechanism stay as ADR-0001 decided.
9. **Versioning.** These are breaking changes, so the next release is v2.0.0.

Alternatives to record: one `support-python` command with subcommands (rejected: the separate commands are what users
and downstream CI call), a global `devops` command (rejected: unpinned release behavior), and centralizing deploy bodies
(rejected: functional divergence, as ADR-0001 found).

### ADR-0001 Update
- Change its Status to "Partially superseded by ADR-0003" with a link, naming which decisions changed.

### Declared Files
- docs/adrs/ADR-0003-standalone-tools-and-reusable-devops.md
- docs/adrs/ADR-0001-devops-scripts-toolkit-scope.md
- docs/requirements.md
- docs/index.md
- CHANGELOG.md
- pyproject.toml
- CLAUDE.md

### Tests
- Unit test: none (documentation and version metadata only; existing version tests cover pyproject and CHANGELOG agreement).
- Integration: `.venv/Scripts/support-python lint markdown check --offline docs CHANGELOG.md CLAUDE.md` exits 0.

Completion check: the integration command above, plus `.venv/Scripts/python -m pytest -q`.
Size estimate: 7 files, 250 lines.
Combined task: the two-line version bump opens the breaking release this ADR justifies and cannot be reviewed meaningfully alone.
