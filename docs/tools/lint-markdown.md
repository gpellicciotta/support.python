# Markdown Linter Rules and Profiles

Automated Markdown style, structure, and link validation implemented in [lint.py](../../src/support_python/markdown/lint.py) and CLI module [lint_markdown.py](../../src/support_python/tools/lint_markdown.py), with rule classes in [rules.py](../../src/support_python/markdown/rules.py), registry in [registry.py](../../src/support_python/markdown/registry.py), and loadable profiles in [profiles.py](../../src/support_python/markdown/profiles.py).

---

## Command-Line Interface
Run Markdown linting through the `lint-markdown` console script in [lint_markdown.py](../../src/support_python/tools/lint_markdown.py):
```bash
lint-markdown check [PATH...] [--format text|json] [--rules IDS] [--profile NAME] [--config PATH] [--plugin ENTRY]... [--offline] [--exclude GLOB]
lint-markdown fix [PATH...] [--dry-run] [--rules IDS] [--profile NAME] [--config PATH] [--plugin ENTRY]... [--offline] [--exclude GLOB]
lint-markdown rules [--format text|json] [--profile NAME] [--config PATH] [--plugin ENTRY]...
lint-markdown config [list|names|path|get|set|delete|edit] [NAME] [VALUE] [--user|--system] [--format text|json]
lint-markdown help [--verbose]
lint-markdown version
```

Supported actions, profile, and rule options:
- `check` lints Markdown files and exits `1` if violations are found; `--format text|json` selects text output or a single JSON object (`{"files_checked": N, "issues": [{"path", "line", "column", "rule_id", "rule_name", "message", "fixable"}]}`) on `stdout`.
- `fix` rewrites files in-place (`MD005`, `MD010`, `MD011`, `MD012`, `MD015`, `MD016`, `MD017`) and then lints; `MD011` allows up to two trailing spaces (a hard line break) and flags longer runs and any trailing tab; `fix` trims longer runs to two spaces and removes trailing tabs; `--dry-run` lists planned fixes without writing and exits `0`.
- `rules` lists every rule with `id`, `name`, `scope`, `fixable`, `enabled` (under the active profile), and `source` (`builtin` or the plugin entry); `--format json` prints `{"rules": [...]}`.
- In `json` mode, log messages go to `stderr` so `stdout` holds only the JSON document.
- `--profile PROFILE` selects a built-in profile (`default` or `dev-guidelines`).
- `--config PATH` loads explicit JSON settings from a `.lint-markdown.json` file, or from the one inside a directory; it replaces the project, user, and system files.
- `--plugin ENTRY` loads extra rules from a plugin file or module (repeatable); see [Rule Plugins](#rule-plugins).
- `--rules RULES` overrides active rules with a comma-separated list of `MD0xx` codes.
- `--exclude GLOB` appends path exclusion globs to the profile and default excludes.
- `--offline` disables external HTTP link checks (`MD018`).
- `config` lists, gets, sets, deletes, and edits settings; it targets the project file `.lint-markdown.json` in the current directory by default, or the user or system file with `--user` or `--system`; see [Settings Sources](#settings-sources).

---

## Built-In Profiles
The profile loader in [profiles.py](../../src/support_python/markdown/profiles.py) provides two built-in profiles:
- `default` enables all 19 rules (`MD001` through `MD019`), matching the Markdown guidelines, without historical-task exemptions.
- `dev-guidelines` enables the same 19 rules and activates `.plan/tasks/` historical-task exemptions.
- On the CLI, omitting both `--profile` and `.lint-markdown.json` selects `default`.
- A `.lint-markdown.json` file that omits the `"profile"` key also uses `default` as its base profile.
- Direct `MarkdownLinter()` calls with `profile=None` enable all 19 rules and historical-task exemptions; pass `profile="default"` to drop the exemptions.

---

## Settings Sources
Each setting comes from the first of these sources that gives a valid value:
1. the command-line option (`--profile` only);
2. the environment variable `LINT_MARKDOWN_{{NAME}}`, such as `LINT_MARKDOWN_DISABLE` or `LINT_MARKDOWN_HISTORICAL_TASK_EXEMPTIONS`;
3. the project file `.lint-markdown.json`, found in the target path or project root (falling back to legacy `.markdown-lint.json` with a deprecation warning until `v3.0.0`);
4. the user file: `$XDG_CONFIG_HOME/lint-markdown/config.json` when `XDG_CONFIG_HOME` is an absolute path, else `%APPDATA%/lint-markdown/config.json` on Windows or `~/.config/lint-markdown/config.json`;
5. the system file: `%PROGRAMDATA%/lint-markdown/config.json` on Windows or `/etc/lint-markdown/config.json`;
6. the built-in default.

List settings (`rules`, `enable`, `disable`, `exclude`, `plugins`, `github-owners`) are replaced as a whole by the first source that sets them; sources never merge their lists.
Environment variables take lists as comma-separated items or a JSON array.
An invalid value, an unreadable or malformed file, or a wrong-typed key warns once and falls through to the next source; unknown keys are ignored and listed with `--debug`.
`--exclude` and `--plugin` stay additive: they append to the resolved `exclude` and `plugins` values.
`--config PATH` replaces files 3 to 5.
Invalid rule IDs or an unknown profile name still exit `2`.

The `config` action reads and writes one file at a time and uses the `.lint-markdown.json` of the current directory as its project file:
```bash
lint-markdown config list --verbose
lint-markdown config set disable MD018
lint-markdown config set profile dev-guidelines --user
lint-markdown config get exclude --source
lint-markdown config path --all
```

---

## JSON Configuration Schema
Configuration keys accept dashes or underscores interchangeably; this document shows the preferred kebab-case spelling.
The same keys work in the project, user, and system files.
```json
{
  "profile": "dev-guidelines",
  "enable": ["MD015"],
  "disable": ["MD018"],
  "historical-task-exemptions": true,
  "excludes": ["archive/*"],
  "plugins": ["rules/no_todo.py"],
  "github-owners": ["gpellicciotta"]
}
```

| Setting                      | Type            | Default         | Environment variable                       | Purpose                                                                              |
| :--------------------------- | :-------------- | :-------------- | :----------------------------------------- | :----------------------------------------------------------------------------------- |
| `profile`                    | `string`        | `"default"`     | `LINT_MARKDOWN_PROFILE`                    | Base profile (`"default"` or `"dev-guidelines"`)                                     |
| `rules`                      | `array<string>` | Profile rules   | `LINT_MARKDOWN_RULES`                      | Explicit rule ID list replacing the profile rules; alias `enabled-rules`             |
| `enable`                     | `array<string>` | `[]`            | `LINT_MARKDOWN_ENABLE`                     | Additional `MD0xx` rule IDs enabled on the profile; alias `enable-rules`             |
| `disable`                    | `array<string>` | `[]`            | `LINT_MARKDOWN_DISABLE`                    | `MD0xx` rule IDs removed from the profile; aliases `disable-rules`, `disabled-rules` |
| `historical-task-exemptions` | `boolean`       | Profile setting | `LINT_MARKDOWN_HISTORICAL_TASK_EXEMPTIONS` | Exempt completed or pre-cutoff `.plan/tasks/` files; alias `historical-tasks`        |
| `exclude`                    | `array<string>` | `[]`            | `LINT_MARKDOWN_EXCLUDE`                    | Additional glob patterns excluded during discovery; alias `excludes`                 |
| `plugins`                    | `array<string>` | `[]`            | `LINT_MARKDOWN_PLUGINS`                    | Rule plugin files or modules loaded before the rules                                 |
| `github-owners`              | `array<string>` | `[]`            | `LINT_MARKDOWN_GITHUB_OWNERS`              | GitHub owners whose repository links resolve to sibling checkouts                    |

The `{ "MD0xx": bool }` map form of `rules` is a library-only feature of `load_profile`; the tool treats it as an invalid value.
Relative plugin paths resolve against the folder of the file that lists them, or the current directory for an environment variable.

---

## Rule Registry
All 19 `MD001`–`MD019` rule classes inherit from `Rule` in [registry.py](../../src/support_python/markdown/registry.py) and register in `DEFAULT_REGISTRY`:
- Look up rules by ID or slug via `DEFAULT_REGISTRY.get("MD001")` or `DEFAULT_REGISTRY.get("heading-increment")`.
- Filter rules in registration order with `DEFAULT_REGISTRY.select(["MD001", "MD017"])`.
- Run a single rule class standalone via `rule.lint(content, file_path=...)`.

---

## Rule Plugins
A plugin is a Python module whose module-level `register(registry)` adds `Rule` instances to the active `RuleRegistry`.
The loader in [plugins.py](../../src/support_python/markdown/plugins.py) uses only the standard library:
- An entry ending in `.py` is a file path, relative to the config file's directory (or the current directory for `--plugin`).
- Any other entry is a dotted module name; it must be importable, for example installed or on `PYTHONPATH`.
- List entries under the `plugins` config key, pass them with repeatable `--plugin ENTRY` options, or both.
- Plugin rules are enabled by default; profile `rules`, `enable`, and `disable` keys apply to them like built-in rules.
- Run `lint-markdown rules` to confirm each plugin rule is registered and enabled.

Write a plugin rule by subclassing `Rule` and returning issues from `check(ctx)`:
```python
import re

from support_python.markdown import LintContext, LintIssue, Rule, RuleRegistry


class NoTodo(Rule):
    rule_id = "X001"
    name = "no-todo"
    description = "Disallow TODO markers in prose."

    def check(self, ctx: LintContext) -> list[LintIssue]:
        match = re.search(r"\bTODO\b", ctx.sanitized)
        if match is None:
            return []
        return [self.issue(ctx, "TODO marker found in prose", column_number=match.start() + 1)]


def register(registry: RuleRegistry) -> None:
    registry.register(NoTodo())
```

The rule's `scope` selects when the linter calls `check(ctx)`:
- `document_pre` and `document_post` run once per file, before and after the line walk, with `ctx.lines` set.
- `raw_line` runs on every line, including front matter and code blocks, with `ctx.line` set.
- `code_fence` runs on each opening code fence, with `ctx.fence_lang` set.
- `heading` runs on each heading outside code blocks, with `ctx.heading_level` and `ctx.heading_title` set.
- `prose` (the default) runs on other lines outside code blocks; `ctx.sanitized` drops code spans and HTML comments.

Use rule IDs that cannot clash with built-in `MD0xx` IDs, such as an `X` prefix.
These plugin problems exit `2` with an error naming the plugin:
- A missing plugin file, or a module that fails to import.
- A module without a callable `register`, or a `register` call that raises.
- A rule ID already registered by a built-in rule or an earlier plugin.
