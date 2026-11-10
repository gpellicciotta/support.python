## Walkthrough & Validation

### Summary of Changes
- Added `support_python.markdown.plugins` with `load_plugins` and `PluginError`.
- Each plugin registers into a staging registry; its rules merge only when none collides.
- Made `.lint-markdown.json` accept a `plugins` key, read through `read_plugin_entries`.
- Made built-in profiles enable plugin rules by default under a plugin-extended registry.
- Added the repeatable `--plugin ENTRY` option and the `rules` action with `--format text|json`.
- Documented plugin authoring in `docs/tools/lint-markdown.md`, and updated README, CHANGELOG, and CLAUDE.md.

### Red Phase
Command: `.venv/Scripts/python -m pytest -q tests/test_markdown_plugins.py` (before implementation), exit code 2.
```text
tests\test_markdown_plugins.py:14: in <module>
    from support_python.markdown.plugins import PluginError, load_plugins
E   ModuleNotFoundError: No module named 'support_python.markdown.plugins'
=========================== short test summary info ===========================
ERROR tests/test_markdown_plugins.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.36s
```

### Green Phase
Command: `.venv/Scripts/python -m pytest -q`, exit code 0.
```text
773 passed, 3 skipped, 81 subtests passed in 100.07s (0:01:40)
```

Commands: `.venv/Scripts/ruff check .` and `.venv/Scripts/ruff format --check .`, exit code 0.
```text
All checks passed!
132 files already formatted
```

### Installed Integration Scenario
The pytest case `test_installed_console_script_loads_plugin_from_config` runs the installed console script in a temporary project.
It runs `lint-markdown check --offline` without paths and `lint-markdown rules --format json`; it passed above.
A manual run used the installed script with `PYTHONPATH` set to the worktree `src`.
The demo directory `work/t0033-demo` holds `.lint-markdown.json` set to `{"plugins": ["rules/no_todo.py"]}`.
It is Git-ignored, so the manual check names `notes.md` explicitly.

Command: `lint-markdown check --offline notes.md`, exit code 1.
```text
notes.md:3:22: X001 [no-todo] TODO marker found in prose
**[WARN]**  Found 1 lint issue across 1 files.
**[ERROR]** Finished lint-markdown check in 0.0s with status: failed
```

Command: `lint-markdown rules --format json`, exit code 0 (X001 entry extracted).
```text
{"id":"X001","name":"no-todo","scope":"prose","fixable":false,"enabled":true,"source":"rules/no_todo.py"}
```

Command: `lint-markdown rules`, exit code 0 (header and X001 row).
```text
id     name                            scope          fixable  enabled  source
X001   no-todo                         prose          no       yes      rules/no_todo.py
```

Command: `lint-markdown check --offline --plugin missing.py`, exit code 2.
```text
**[ERROR]** Plugin 'missing.py': file not found: {{worktree}}/work/t0033-demo/missing.py
**[ERROR]** Finished lint-markdown check in 0.0s with status: failed
```

Command: `lint-markdown check --offline docs/tools/lint-markdown.md`, exit code 0.
```text
All 1 markdown files passed linting.
```
