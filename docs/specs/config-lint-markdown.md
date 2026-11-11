# Specification: `.lint-markdown.json`

Configuration file format of `lint-markdown`.
Implemented in [profiles.py](../../src/support_python/markdown/profiles.py).
Usage is in [lint-markdown.md](../tools/lint-markdown.md).

---

## Files and Precedence
Each setting takes the first valid value from these sources:
1. The command-line option, where one exists.
2. The environment variable `LINT_MARKDOWN_{{NAME}}`, such as `LINT_MARKDOWN_PROFILE`.
3. The project file `.lint-markdown.json`.
4. The user file `{{user-config-dir}}/lint-markdown/config.json`.
5. The system file `%PROGRAMDATA%/lint-markdown/config.json` on Windows, `/etc/lint-markdown/config.json` elsewhere.
6. The built-in default.

- `--config PATH` replaces discovery of the three files; a directory resolves to the file inside it.
- The project file is searched in each target path, then the Git root, then the current directory.
- The legacy project file `.markdown-lint.json` is read with a warning when `.lint-markdown.json` is absent.
  It is removed in v3.0.0.
- List settings replace across sources; they do not merge.
- `{{user-config-dir}}` is `$XDG_CONFIG_HOME` when absolute, else `%APPDATA%` on Windows, else `~/.config`.

## File Shape
- The file holds one UTF-8 JSON object.
- Keys use `kebab-case` or `snake_case`; both spellings are equal.
  When one file sets both, the `kebab-case` value wins and a warning is logged.
- Unknown keys are ignored and listed at debug level.
- A malformed file, a non-object file, or a wrongly typed value warns and falls through to the next source.
- List environment values take comma-separated items or a JSON array.

## Settings
| Key                          | Type    | Default       | Aliases                           | Meaning                                       |
| :--------------------------- | :------ | :------------ | :-------------------------------- | :-------------------------------------------- |
| `profile`                    | string  | `default`     |                                   | Base profile: `default` or `dev-guidelines`   |
| `rules`                      | list    | profile rules | `enabled-rules`                   | Explicit rule IDs, replacing the profile      |
| `enable`                     | list    | `[]`          | `enable-rules`                    | Rule IDs enabled on top of the profile        |
| `disable`                    | list    | `[]`          | `disable-rules`, `disabled-rules` | Rule IDs removed from the profile             |
| `historical-task-exemptions` | boolean | per profile   | `historical-tasks`                | Exempt completed `.plan/tasks/` files         |
| `exclude`                    | list    | `[]`          | `excludes`                        | Glob patterns excluded during file discovery  |
| `plugins`                    | list    | `[]`          |                                   | Rule plugin files or dotted module names      |
| `github-owners`              | list    | `[]`          |                                   | Owners whose repository links resolve locally |

- Rule entries are rule IDs such as `MD001` or rule names such as `aligned-tables`; unknown rules are errors.
- Rules apply in this order: `rules`, then `enable`, then `disable`.
- The `dev-guidelines` profile turns historical task exemptions on; `default` leaves them off.
- A `plugins` entry ending in `.py` is a file path, relative to the folder of the file that sets it.
  Any other entry is an importable module name.
- Each plugin defines a callable `register(registry)`.
- The mapping form of `rules` (`{"MD001": false}`) is library-only; the file takes a list.

## Example
```json
{
  "profile": "dev-guidelines",
  "enable": ["MD019"],
  "disable": ["MD013"],
  "exclude": ["node_modules/**", "CHANGELOG.md"],
  "plugins": ["tools/lint-rules.py"],
  "github-owners": ["my-org"]
}
```
