### Plugin Entries
- An entry ending in `.py` is a file path, relative to the config file's directory (or the current directory for `--plugin`),
  loaded with `importlib.util.spec_from_file_location` under a unique module name.
- Any other entry is a dotted module name, loaded with `importlib.import_module`.
- No entry-point discovery and no third-party dependencies.

### Plugin Contract
```python
from support_python.markdown import Rule, RuleRegistry

class NoTodo(Rule):
    rule_id = "X001"
    name = "no-todo"
    description = "Disallow TODO markers in prose."

    def check(self, ctx):
        ...

def register(registry: RuleRegistry) -> None:
    registry.register(NoTodo())
```
- Plugin rules are enabled by default; profile `enable` and `disable` keys apply to them like built-in rules.
- Errors exiting 2, each naming the plugin: missing file, import failure, missing `register`, an exception in `register`,
  and a rule ID that collides with a registered rule.

### rules Action
- `lint-markdown rules [--format text|json] [--config PATH] [--plugin ENTRY]...`
- Columns or keys: `id`, `name`, `scope`, `fixable`, `enabled` (under the active profile), and `source` (`builtin` or the plugin entry).

### Declared Files
- src/support_python/markdown/plugins.py
- src/support_python/markdown/profiles.py
- src/support_python/tools/lint_markdown.py
- tests/test_markdown_plugins.py
- tests/fixtures/markdown_plugins/no_todo.py
- docs/tools/lint-markdown.md
- README.md
- CHANGELOG.md

### Tests
- Unit: a path plugin and a dotted-module plugin each register a rule that then reports issues.
- Unit: a duplicate rule ID, a missing `register`, and an import failure each exit 2 naming the plugin.
- Unit: a profile `disable` entry turns a plugin rule off.
- Unit: the `rules` action lists built-in and plugin rules in text and JSON.
- Integration: in a temporary project with `.lint-markdown.json` set to `{"plugins": ["rules/no_todo.py"]}` and a Markdown file containing
  `TODO`, installed `lint-markdown check --offline` exits 1 reporting `X001`, and `lint-markdown rules --format json` includes it.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration scenario above.
Size estimate: 8 files, 400 lines.
