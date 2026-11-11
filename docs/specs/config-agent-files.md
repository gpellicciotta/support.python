# Specification: `.agent-files.json`

Configuration file format of `agent-files`.
Implemented in [agent_files_config.py](../../src/support_python/tools/agent_files_config.py).
Usage is in [agent-files.md](../tools/agent-files.md).

---

## Files and Precedence
Each setting takes the first valid value from these sources:
1. The command-line option, where one exists.
2. The environment variable `AGENT_FILES_{{NAME}}`, such as `AGENT_FILES_REPO_ROOT`.
3. The project file `.agent-files.json` in the repository root.
4. The user file `{{user-config-dir}}/agent-files/config.json`.
5. The system file `%PROGRAMDATA%/agent-files/config.json` on Windows, `/etc/agent-files/config.json` elsewhere.
6. The built-in default.

- `--config PATH` replaces discovery of the three files.
- `{{user-config-dir}}` is `$XDG_CONFIG_HOME` when absolute, else `%APPDATA%` on Windows, else `~/.config`.
- The legacy project file `agent-files.json` is read with a warning when `.agent-files.json` is absent.
  It is removed in v3.0.0.
- Dictionary settings (`tools`) merge key by key across sources; the highest source wins per key.
- Other values replace; they do not merge.

## File Shape
- The file holds one UTF-8 JSON object.
- Keys use `kebab-case` or `snake_case`; both spellings are equal.
  When one file sets both, the `kebab-case` value wins and a warning is logged.
- Unknown keys are ignored and listed at debug level.
- A malformed file, a non-object file, or a wrongly typed value warns and falls through to the next source.
- List environment values take comma-separated items or a JSON array.

## Settings
| Key                  | Type    | Default                      | Meaning                                                           |
| :------------------- | :------ | :--------------------------- | :---------------------------------------------------------------- |
| `repo-root`          | string  | Git root of the project file | Repository root; a relative path resolves against the file folder |
| `digest-path`        | string  | `agent-digest.md`            | Digest file to install; alias `digest`                            |
| `skills-dir`         | string  | `agent-skills`               | Skills directory to install; alias `skills`                       |
| `marker`             | string  | `dev-guidelines`             | Identifier of the guarded block comments                          |
| `marker-begin`       | string  | derived from `marker`        | Explicit opening guarded block line                               |
| `marker-end`         | string  | derived from `marker`        | Explicit closing guarded block line                               |
| `manifest-source`    | string  | `dev-guidelines`             | Ownership source recorded in the skills manifests                 |
| `manifest-name`      | string  | derived from the source      | Manifest file name inside each target skills folder               |
| `legacy-skill-names` | list    | built-in list                | Bootstrap skill names owned before a manifest exists              |
| `replace-tools`      | boolean | `false`                      | Replace the built-in tools instead of merging into them           |
| `tools`              | dict    | `{}`                         | Tool definitions by name                                          |

- `digest-path` and `skills-dir` resolve relative paths against `repo-root`.
- `digest-path`, `skills-dir`, `marker`, and `manifest-source` must be non-empty strings.
- `manifest-name` defaults to `.dev-guidelines-skills.json` for the default source, else `.{{manifest-source}}-skills.json`.
- `legacy-skill-names` defaults to `plan-task-usage` and `ui-verification` for the default source, else empty.

## The `tools` Setting
`tools` maps a tool name to a definition object.
A file may also give a list of objects that each carry a `name`; the list converts to the object form.
The environment variable `AGENT_FILES_TOOLS` takes a JSON array or object as text.
A definition with the name of a built-in tool replaces that tool.

| Key                      | Type         | Required | Meaning                                                  |
| :----------------------- | :----------- | :------- | :------------------------------------------------------- |
| `name`                   | string       | yes      | Tool name; implied by the object key in the object form  |
| `command`                | string       | yes      | Executable name used to detect the tool                  |
| `target_file`            | string       | yes      | Global instructions file that receives the guarded block |
| `review_args`            | list[string] | no       | Headless review arguments; empty when omitted            |
| `fallback_paths`         | list[string] | no       | Executable paths tried when `command` is not on `PATH`   |
| `skills_dir`             | string, null | no       | Skills directory; `null` means the tool has none         |
| `native_skill_discovery` | boolean      | no       | Tool finds skills itself; default `false`                |
| `legacy_skills_dirs`     | list[string] | no       | Old skills directories to clean up                       |
| `bootstrap_skill_names`  | list[string] | no       | Skill names owned before a manifest exists               |
| `aliases`                | list[string] | no       | Alternative names accepted on the command line           |

- Tool keys are the `snake_case` names above; `kebab-case` spellings are accepted.
- Any other key is an error: `tool '{{name}}' has unknown keys`.
- Paths expand `~`.
- `review_args` entries may use the placeholders `{prompt}`, `{target_file}`, and `{timeout}`.

## Example
```json
{
  "repo-root": ".",
  "digest-path": "agent-digest.md",
  "skills-dir": "agent-skills",
  "marker": "dev-guidelines",
  "replace-tools": false,
  "tools": {
    "my-assistant": {
      "command": "my-assistant",
      "target_file": "~/.my-assistant/INSTRUCTIONS.md",
      "skills_dir": "~/.my-assistant/skills",
      "native_skill_discovery": true,
      "review_args": ["--prompt", "{prompt}", "--timeout", "{timeout}"],
      "aliases": ["assistant"]
    }
  }
}
```

## Errors
- `FileNotFoundError`: `--config` names a file that does not exist.
- `ValueError`: a resolved path or string is empty, or a tool definition is invalid.
