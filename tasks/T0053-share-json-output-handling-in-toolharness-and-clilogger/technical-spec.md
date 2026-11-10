### Current Implementations to Replace
| Tool                    | Mechanism                                                                 | In JSON mode, INFO goes to | WARN/ERROR go to |
|-------------------------|---------------------------------------------------------------------------|----------------------------|------------------|
| `agent-files`           | `StderrRoutingLogger` + `SyncHarness.create_logger`/completion override    | dropped                    | stderr           |
| `lint-markdown`         | `_JsonAwareLogger` + harness `create_logger` override                      | dropped                    | stderr           |
| `processes`             | `JsonModeLogger` + `ProcessesHarness.create_logger`                        | stderr                     | stderr           |
| `git-repository-backup` | `BackupHarness.log_startup`/`log_completion` JSON branches with `to_stdout=False` | dropped               | stderr           |

### Shared Behavior
- **Rule: in JSON mode, redirect, never drop.** Every message that would reach stdout goes to stderr instead.
  Messages already bound for stderr stay there. File logging is unchanged.
- Banners keep their normal verbosity rules; they just move to stderr in JSON mode.
- This unifies on the `processes` behavior; agent-files, lint-markdown, and git-repository-backup now show on stderr the INFO
  lines they used to drop. List this in `CHANGELOG.md` as a behavior change, not a breaking one.

### API
```python
class CliLogger:
    json_output: bool = False          # set by ToolHarness; when True, stdout is reserved for emit_json
    def emit_json(self, payload: Any, *, indent: int | None = None) -> None
        # writes json.dumps(payload, indent=indent) plus a newline to stdout, also in JSON mode

class ToolHarness:
    @staticmethod
    def add_format_option(parser: argparse.ArgumentParser, *, default: str = "text") -> None
        # adds --format {text,json} with the standard help text
    # create_logger(args) sets logger.json_output = (getattr(args, "format", None) == "json")
```
- Put the routing in `CliLogger.log`, so tools need no logger subclass.
- `emit` keeps writing to stdout unchanged; tools printing JSON switch to `emit_json`, or to `emit` with an already-serialized document.
- Keep each tool's serialization: agent-files and git-repository-backup use `indent=2`, lint-markdown uses compact output,
  and processes keeps `render_output`'s JSON.

### Tool Changes
- Delete `StderrRoutingLogger`, `_JsonAwareLogger`, `JsonModeLogger`, `ProcessesHarness` (if nothing else remains in it),
  and the JSON branches in `BackupHarness.log_startup`, `BackupHarness.log_completion`, and `SyncHarness` completion logging.
- Register `--format` through `ToolHarness.add_format_option` in all four tools.
- agent-digest gains JSON output in T0048, which must use this shared mode.

### Declared Files
- src/support_python/logging.py
- src/support_python/cli.py
- src/support_python/tools/agent_files.py
- src/support_python/tools/lint_markdown.py
- src/support_python/tools/processes.py
- src/support_python/tools/git_repository_backup.py
- tests/test_cli.py
- tests/test_logging.py
- CHANGELOG.md
- docs/tools/agent-files.md, docs/tools/lint-markdown.md, docs/tools/git-repository-backup.md (JSON-mode stderr note)
- docs/tutorials/cli-harness-and-logging.md (shared JSON mode example)
- tests/tools/test_agent_files.py (retarget `StderrRoutingLogger` uses to `CliLogger`; one stderr assertion)

### Tests
- Unit: with `json_output` set, `info`, `warn`, `error`, `debug_msg`, and banners write nothing to stdout and reach stderr per the redirect rule.
- Unit: `emit_json` writes exactly one JSON document and newline to stdout, honoring `indent`.
- Unit: `ToolHarness` sets `json_output` only when the parsed action has `--format json`; `add_format_option` adds the standard option.
- Unit: no module under `src/support_python/tools/` defines a `CliLogger` subclass (source scan).
- Unit: the existing tool suites pass unchanged apart from assertions on stderr INFO lines that are now redirected instead of dropped.
- Integration: installed `processes list --format json`, `agent-files list --format json`, `lint-markdown check --offline --format json docs`,
  and `git-repository-backup list --format json --root <tmp>` each print stdout that `json.loads` parses, with banners on stderr under `--verbose`.
- Integration: `lint-markdown check --format json <missing-path>` exits 2 with an error on stderr and empty stdout.

Completion check: `.venv/Scripts/python -m pytest -q`, `.venv/Scripts/ruff check .`, plus the integration checks above.
Size estimate: 9 files, 350 lines.
Size note: above 8 files because the shared mode replaces four private copies; deleting them is the point of the task.

### Environment
- Run install-dependent checks in a worktree-local venv: `python -m venv .venv`, then `.venv/Scripts/pip install -e ".[dev]"` inside the task worktree.
- Never reinstall the primary checkout's `.venv` from a worktree; its editable install must keep pointing at the primary checkout.
