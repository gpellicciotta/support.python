<!-- BEGIN plan (managed by plan init) -->
This project tracks its work with plan in `PLAN.md` and `.plan/tasks/`.
Load the `plan-task-usage-guidelines` skill before creating, starting, or changing tasks.
Change `PLAN.md` and task frontmatter only through `plan` commands.
<!-- END plan -->

# support-python
A general-purpose Python library and five console tools for Python clients and ops scripts, with no runtime dependencies.
It ships `processes`, `agent-files`, `agent-digest`, `lint-markdown`, and `git-repository-backup`, plus the `support_python` library.
See [README.md](README.md) for usage, [index.md](docs/index.md) for all documentation, and [devops.md](docs/devops.md) for operations.
[migration-v2.md](docs/migration-v2.md) maps every v1.x name to its v2.0.0 replacement.

## Commands
- Bootstrap a fresh checkout: `python scripts/bootstrap-dev-environment.py`
- Run the tests: `python scripts/devops.py test` (a selection: `python scripts/devops.py test tests/test_cli.py`)
- Run all checks (lint, tests, build): `python scripts/devops.py check`
- Reformat sources: `python scripts/devops.py format`
- Lint Markdown: `.venv/Scripts/lint-markdown check --offline` (`.venv/bin/` outside Windows)
- Run a tool from the checkout: `.venv/Scripts/{{tool-name}} help --verbose`

## Architecture
- [src/support_python/](src/support_python/): the library; public symbols are re-exported from the package root.
- [cli.py](src/support_python/cli.py), [logging.py](src/support_python/logging.py): `ToolHarness` and `CliLogger`, the base of every tool.
- [config.py](src/support_python/config.py), [env.py](src/support_python/env.py): settings resolver, `config` command group, and config paths.
- [net.py](src/support_python/net.py), [errors.py](src/support_python/errors.py), [dates.py](src/support_python/dates.py), [models.py](src/support_python/models.py): REST-client transport and wire helpers.
- [git.py](src/support_python/git.py), [processes.py](src/support_python/processes.py), [files.py](src/support_python/files.py), [locking.py](src/support_python/locking.py): Git, process, file, and lock helpers.
- [markdown/](src/support_python/markdown/): table formatting and the rule-based Markdown linter.
- [devops/](src/support_python/devops/): `DevopsCli`, project adapters, release, deploy, and service managers.
- [tools/](src/support_python/tools/): the five console tools; not re-exported from the package root.
- [scripts/](scripts/): bootstrap, `devops.py`, and one-off repository maintenance scripts.
- [tests/](tests/): pytest suite; [tests/tools/](tests/tools/) covers the console tools.
- [docs/tools/](docs/tools/) and [docs/tutorials/](docs/tutorials/): per-tool references and library tutorials.

## Project Conventions
- Keep `dependencies` in [pyproject.toml](pyproject.toml) empty; optional backends go in extras such as `redis` and `mysql`.
- Support Python 3.9: use `from __future__ import annotations` and `typing.Optional`/`Union` in annotations.
- Use a 132-character line length, enforced by `ruff` and [.editorconfig](.editorconfig).
- Build every console tool on `ToolHarness` and `CliLogger` instead of `argparse` and `print`.
- Load `support_python` from `src/` in [devops.py](scripts/devops.py); this repository cannot pin itself in `scripts/requirements.txt`.
- Keep [bootstrap-dev-environment.py](scripts/bootstrap-dev-environment.py) and [_cli_common.py](scripts/_cli_common.py) stdlib-only, without importing `support_python`.
- Record every breaking v2 change in [migration-v2.md](docs/migration-v2.md) as well as in [CHANGELOG.md](CHANGELOG.md).
- Treat `tests/fixtures/agent_digest/` as a frozen dev-guidelines snapshot; change it only to test new digest behavior.

## Boundaries
- Never run `agent-files sync` or `agent-files review` without `--dry-run`; they write the user's global agent files.
- Never run [reset-history.py](scripts/reset-history.py) or the outbound steps of [migrate-namespace.py](scripts/migrate-namespace.py); they rewrite history and remotes.
- Never run `python scripts/devops.py release` without `--dry-run` unless the user asks for a release.
- Never add a runtime dependency without the user's approval.
- Never let tests read or write real user state, such as `~/.claude/` or the repository's own `.plan/`. A conftest guard fails the test run on leaks.
