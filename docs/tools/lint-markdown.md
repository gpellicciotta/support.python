# Markdown Linter Rules and Profiles

Automated Markdown style, structure, and link validation implemented in [lint.py](../../src/support_python/markdown/lint.py) and CLI module [lint_markdown.py](../../src/support_python/tools/lint_markdown.py), with rule classes in [rules.py](../../src/support_python/markdown/rules.py), registry in [registry.py](../../src/support_python/markdown/registry.py), and loadable profiles in [profiles.py](../../src/support_python/markdown/profiles.py).

---

## Command-Line Interface
Run Markdown linting through the `lint-markdown` console script in [lint_markdown.py](../../src/support_python/tools/lint_markdown.py):
```bash
lint-markdown [check|fix] [PATH ...] [--profile PROFILE] [--config PATH] [--rules RULES] [--offline] [--fix]
```

Supported profile and rule options:
- `--profile PROFILE` selects a built-in profile (`default` or `dev-guidelines`).
- `--config PATH` loads explicit JSON settings from a `.markdown-lint.json` file.
- `--rules RULES` overrides active rules with a comma-separated list of `MD0xx` codes.
- `--exclude GLOB` appends path exclusion globs to the profile and default excludes.
- `--offline` disables external HTTP link checks (`MD018`).
- `--fix` applies safe formatting fixes in-place (`MD005`, `MD010`, `MD011`, `MD012`, `MD015`, `MD016`, `MD017`).

---

## Built-In Profiles
The profile loader in [profiles.py](../../src/support_python/markdown/profiles.py) provides two built-in profiles:
- `default` enables generic rules (`MD001` through `MD014` and `MD016` through `MD019`), leaving `MD015` and historical-task exemptions disabled.
- `dev-guidelines` enables all 19 rules (`MD001` through `MD019`, including `MD015`) and activates `.plan/tasks/` historical-task exemptions.
- On the CLI, omitting both `--profile` and `.markdown-lint.json` selects `default`.
- A `.markdown-lint.json` file that omits the `"profile"` key also uses `default` as its base profile.
- Direct `MarkdownLinter()` calls with `profile=None` enable all 19 rules and historical-task exemptions; pass `profile="default"` for the generic profile.

---

## JSON Configuration Schema
When `--config` is omitted, the CLI discovers `.markdown-lint.json` in the target path or project root, falling back to `default` when absent.
```json
{
  "profile": "dev-guidelines",
  "enable": ["MD015"],
  "disable": ["MD018"],
  "historical_task_exemptions": true,
  "excludes": ["archive/*"]
}
```

| Field                        | Type                      | Default          | Purpose                                               |
| :--------------------------- | :------------------------ | :--------------- | :---------------------------------------------------- |
| `profile`                    | `string`                  | `"default"`      | Base profile (`"default"` or `"dev-guidelines"`)      |
| `rules` / `enabled_rules`    | `array<string> \| object` | Profile rules    | Explicit rule ID list or `{ "MD0xx": bool }` map      |
| `enable` / `enable_rules`    | `array<string>`           | `[]`             | Additional `MD0xx` rule IDs enabled on the profile    |
| `disable` / `disable_rules`  | `array<string>`           | `[]`             | `MD0xx` rule IDs removed from the profile             |
| `historical_task_exemptions` | `boolean`                 | Profile setting  | Exempt completed or pre-cutoff `.plan/tasks/` files   |
| `excludes` / `exclude`       | `array<string>`           | `[]`             | Additional glob patterns excluded during discovery    |

---

## Rule Registry
All 19 `MD001`–`MD019` rule classes inherit from `Rule` in [registry.py](../../src/support_python/markdown/registry.py) and register in `DEFAULT_REGISTRY`:
- Look up rules by ID or slug via `DEFAULT_REGISTRY.get("MD001")` or `DEFAULT_REGISTRY.get("heading-increment")`.
- Filter rules in registration order with `DEFAULT_REGISTRY.select(["MD001", "MD017"])`.
- Run a single rule class standalone via `rule.lint(content, file_path=...)`.
