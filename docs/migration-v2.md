# Migrating to support-python v2.0.0

Map every v1.x command, module, option, verb, config file, and API to its v2.0.0 replacement.
Version 2.0.0 replaces the `support-python` umbrella command with five standalone console scripts.
It moves tool modules into `support_python.tools` and turns `support_python.devops` into a reusable package.
[ADR-0003-standalone-tools-and-reusable-devops.md](adrs/ADR-0003-standalone-tools-and-reusable-devops.md) records the rationale.
The `**[breaking]**` entries in the [CHANGELOG](../CHANGELOG.md) list each change.

---

## Installing the Tools
Install the five tools (`processes`, `agent-files`, `agent-digest`, `lint-markdown`, `git-repository-backup`) per user:
```bash
pipx install "git+https://github.com/gpellicciotta/support.python.git@v2.0.0"
uv tool install "git+https://github.com/gpellicciotta/support.python.git@v2.0.0"
pip install --user "git+https://github.com/gpellicciotta/support.python.git@v2.0.0"
python scripts/install-from-github-release.py 2.0.0 --global
```

Repository scripts keep pinning the library in their own `scripts/requirements.txt`:
```text
support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0
```

---

## Commands
Every tool now runs under its own name; `support-python` and the wrapper scripts are gone.

| v1.x command                                      | v2.0.0 replacement                                                 |
| :------------------------------------------------ | :----------------------------------------------------------------- |
| `support-python lint markdown [PATH...]`          | `lint-markdown check [PATH...]`                                    |
| `support-python lint markdown --fix [PATH...]`    | `lint-markdown fix [PATH...]`                                      |
| `support-python agent-files ACTION`               | `agent-files ACTION`                                               |
| `support-python backup ACTION`                    | `git-repository-backup ACTION`                                     |
| `support-python greet`                            | Removed, with no replacement                                       |
| `support-python --version` / `--help`             | `TOOL version` / `TOOL help` on each standalone tool               |
| `python -m support_python`                        | Removed, with no replacement                                       |
| `python scripts/processes.py ACTION`              | `processes ACTION`                                                 |
| `python scripts/lint-markdown.py ACTION`          | `lint-markdown ACTION`                                             |
| `python scripts/agent-files.py ACTION`            | `agent-files ACTION`                                               |
| `python scripts/backup-git-repos.py ACTION`       | `git-repository-backup ACTION`                                     |
| dev-guidelines `scripts/generate-agent-digest.py` | `agent-digest generate <PATH>...` / `agent-digest check <PATH>...` |

[extract-release-notes.py](../scripts/extract-release-notes.py), [migrate-namespace.py](../scripts/migrate-namespace.py), and [reset-history.py](../scripts/reset-history.py) now act on the current directory's repository.
`migrate-namespace.py finish` also publishes the frozen section as release notes.

---

## Verbs and Options
Every tool exits `0` on success, `1` on failure or `check` findings, and `2` on invalid arguments.
Dry runs and JSON output are available on these actions in v2.0.0:
- `--dry-run`: `agent-files sync`, `lint-markdown fix`, `processes kill`, and the `git-repository-backup` writing actions.
- `--format text|json`: `agent-files list` and `check`, `lint-markdown check` and `rules`, `processes list`, and `git-repository-backup list`.
- `json` mode prints one document on `stdout`.
- `agent-digest` accepts neither option yet: `generate` always writes, and `check` prints text only.

| Tool                    | v1.x                                            | v2.0.0                                                        |
| :---------------------- | :---------------------------------------------- | :------------------------------------------------------------ |
| `agent-files`           | `update`                                        | `sync`                                                        |
| `agent-files`           | `diff`                                          | `check`                                                       |
| `agent-files`           | `sync` regenerates `guidelines/agent-digest.md` | Run `agent-digest generate` first; a missing digest exits `1` |
| `agent-files`           | Digest `guidelines/agent-digest.md`             | `./agent-digest.md`, or `--digest PATH` / `digest_path`       |
| `agent-files`           | Skills directory `skills/`                      | `./agent-skills`, or `--skills-dir PATH` / `skills_dir`       |
| `agent-digest`          | `generate` / `check` over fixed inputs          | `generate <PATH>...` / `check <PATH>...`                      |
| `agent-digest`          | `validate`                                      | `check <PATH>...`                                             |
| `agent-digest`          | Output `guidelines/agent-digest.md`, `skills/`  | `--digest PATH` and `--skills-dir PATH`                       |
| `lint-markdown`         | `check --fix`                                   | `fix`, with `fix --dry-run` to preview                        |
| `processes`             | `list --format table`                           | `list --format text`; `table` now exits `2`                   |
| `processes`             | No dry run                                      | `kill --dry-run`                                              |
| `git-repository-backup` | Text-only `list`                                | `list --format text` or `list --format json`                  |
| Capture CLIs            | `-v` shows the version                          | `-v` means `--verbose`; use `--version`                       |
| Capture CLIs            | No arguments runs the default action            | No arguments shows help; invalid arguments exit `2`           |

`agent-digest` orders its inputs by integer `index` front-matter; see [agent-digest.md](tools/agent-digest.md).
To keep the v1.x dev-guidelines layout, pass the old paths explicitly:
```bash
agent-digest generate guidelines --digest guidelines/agent-digest.md --skills-dir skills
agent-files sync --digest guidelines/agent-digest.md --skills-dir skills
```

---

## Configuration Files
Each tool reads its legacy path with a deprecation warning until `v3.0.0`; rename the file now.

| v1.x path                                | v2.0.0 path                                   |
| :--------------------------------------- | :-------------------------------------------- |
| `.markdown-lint.json`                    | `.lint-markdown.json`                         |
| `agent-files.json`                       | `.agent-files.json`                           |
| `~/.config/backup-git-repos/config.json` | `git-repository-backup` user config file      |

The `git-repository-backup` user config file location is listed in [git-repository-backup.md](tools/git-repository-backup.md#configuration-discovery-and-schema).
Configuration keys in every tool accept kebab-case and snake_case spellings, so existing files keep working; docs use kebab-case.
`--config PATH` still overrides discovery on every tool that reads configuration.

---

## Modules
Tool modules moved into `support_python.tools` and are no longer re-exported from the package root.

| v1.x module                         | v2.0.0 module                                                                     |
| :---------------------------------- | :-------------------------------------------------------------------------------- |
| `support_python.markdown_lint`      | `support_python.markdown` (engine) and `support_python.tools.lint_markdown` (CLI) |
| `support_python.cli_processes`      | `support_python.tools.processes`                                                  |
| `support_python.agent_files`        | `support_python.tools.agent_files`                                                |
| `support_python.agent_files_config` | `support_python.tools.agent_files_config`                                         |
| `support_python.backup`             | `support_python.tools.git_repository_backup`                                      |
| `support_python.__main__`           | Removed, with no replacement                                                      |
| `support_python.devops` (module)    | `support_python.devops` package; existing imports keep working                    |

The `support_python.devops` split moves mock patch targets:

| v1.x patch target                      | v2.0.0 patch target                             |
| :------------------------------------- | :---------------------------------------------- |
| `support_python.devops.<step helper>`  | `support_python.devops.steps.<step helper>`     |
| `support_python.devops.<service name>` | `support_python.devops.services.<service name>` |
| `support_python.devops.is_port_in_use` | `support_python.devops.services.is_port_in_use` |
| `support_python.devops.signal.signal`  | `support_python.devops.services.signal.signal`  |

---

## Library API
Removed names and their replacements:

| v1.x API                                 | v2.0.0 replacement                                        |
| :--------------------------------------- | :-------------------------------------------------------- |
| `ToolLogger`, `TeeLogger`                | `CliLogger`                                               |
| `build_action_parser`                    | `ToolHarness` with `add_action`                           |
| `print_help`, `print_version`            | The harness `help` and `version` actions                  |
| `format_version`                         | `ToolHarness.format_version()`                            |
| `format_support_message`                 | Removed, with no replacement                              |
| `build_capture_parser`                   | `build_capture_harness`                                   |
| `configure_utf8_output()` in tool `main` | Drop the call; `ToolHarness.run` configures UTF-8 streams |

`run_capture_cli` log lines no longer carry a `cli_name` origin.
`MarkdownLinter`, `LintIssue`, `RuleRegistry`, `LintProfile`, and `load_profile` import from `support_python.markdown` or the package root.

A v1.x `build_action_parser` script becomes a `ToolHarness`:
```python
import sys

from support_python import CliLogger
from support_python.cli import ToolHarness


def greet(args, logger: CliLogger) -> int:
    logger.info("Hello")
    return 0


harness = ToolHarness("my-tool", "Describe the tool in one sentence.")
harness.add_action("greet", "print a greeting", greet)
sys.exit(harness.run())
```

---

## Migrating `scripts/devops.py`
Replace a hand-written `devops.py` with a thin script over `DevopsCli` and the matching project adapter.
`DevopsCli` provides `lint`, `format`, `test`, `build`, `check`, `clean`, `versions`, and `release`.
Keep the script in `scripts/` and install `support_python` from `scripts/requirements.txt`, as [ADR-0001-devops-scripts-toolkit-scope.md](adrs/ADR-0001-devops-scripts-toolkit-scope.md) requires.

| Project type   | Adapter                    | Version file        | Release assets                           |
| :------------- | :------------------------- | :------------------ | :--------------------------------------- |
| Python (venv)  | `PythonProject(REPO_ROOT)` | `pyproject.toml`    | `dist/*` wheel and sdist                 |
| Gradle wrapper | `GradleProject(REPO_ROOT)` | `gradle.properties` | `build/libs/*.jar`, `*/build/libs/*.jar` |
| npm            | `NodeProject(REPO_ROOT)`   | `package.json`      | `dist/*.tgz`                             |

A Python, Gradle, or npm project needs only this script:
```python
#!/usr/bin/env python3
import sys
from pathlib import Path

from support_python.devops import DevopsCli, GradleProject

REPO_ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    sys.exit(DevopsCli(GradleProject(REPO_ROOT)).run())
```

`GradleProject` takes task-list overrides such as `lint_tasks`, and `release_task` to delegate `devops release`.
Server projects replace their duplicated docker, db, server, mail, client, and production code:
- `add_services(...)` registers the `docker`, `db`, `server`, `mail`, and `client` action groups from the service managers.
- `set_deploy(steps, verify=...)` adds `deploy`, which checks preconditions, asks for typed confirmation, and runs `DeployStep`s.
- Deploy step bodies stay project-local, as ADR-0001 decided.

```python
cli = DevopsCli(GradleProject(REPO_ROOT))
server = LocalServerManager(port=8080, repo_root=REPO_ROOT, app_name="Todos")
cli.add_services(
    docker=LocalDockerManager(),
    mysql=LocalMySqlManager(container_name="todos-mysql", repo_root=REPO_ROOT),
    server=server,
    mail=LocalMailManager(server_manager=server),
    verifier=LocalVerifier(port=8080),
)
cli.set_deploy([DeployStep("push image", command=["docker", "push", IMAGE])], verify=check_live_version)
sys.exit(cli.run())
```

Keep project-specific actions with `add_action(name, summary, handler)`, where `handler(args, logger)` returns an exit code.
The [DevOps scripts tutorial](tutorials/devops-scripts.md) documents every option and sub-action.
