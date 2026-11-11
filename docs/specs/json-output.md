# Specification: JSON Output Documents

Every `--format json` document of the five tools and the shared `config` command group.
Sources are the tool modules in [tools/](../../src/support_python/tools/) and [config.py](../../src/support_python/config.py).

---

## Common Rules
- Each invocation prints exactly one JSON document and a newline on `stdout`.
- Log messages go to `stderr` in JSON mode.
- Field names use `snake_case`; status values use `kebab-case`.
- Paths are strings; tools show them relative to the repository root or current directory when possible.
- Optional fields are omitted, never `null`, unless a field table says `null` is possible.
- The exit code follows the text mode: `0` for success, `1` for findings or failures, `2` for invalid arguments.
- A run that fails before it has results, such as invalid arguments, prints no document.
- Indentation is not part of the contract; parse the output.

## `processes`
### `list`
An array of process objects; `[]` when nothing matches.

| Field     | Type         | Meaning                                              |
| :-------- | :----------- | :--------------------------------------------------- |
| `pid`     | integer      | Process ID                                           |
| `ppid`    | integer      | Parent process ID                                    |
| `name`    | string       | Executable name                                      |
| `started` | string, null | ISO 8601 start time; `null` when unknown             |
| `cwd`     | string, null | Working directory; `null` when unknown or unreadable |

```json
[
  {"pid": 4120, "ppid": 1032, "name": "python.exe", "started": "2026-11-11T09:14:02", "cwd": "C:\\work\\app"}
]
```

### `kill`
An array with one entry per PID, in argument order.
`kill --dry-run` uses the same shape.

| Field     | Type    | Meaning                                |
| :-------- | :------ | :------------------------------------- |
| `pid`     | integer | Requested process ID                   |
| `outcome` | string  | See the table below                    |
| `detail`  | string  | Failure message; present when `failed` |

| Outcome                | Mode    | Meaning                                      |
| :--------------------- | :------ | :------------------------------------------- |
| `killed`               | kill    | The process was terminated                   |
| `skipped-protected`    | kill    | The PID is this tool or one of its ancestors |
| `not-found`            | kill    | No such process                              |
| `failed`               | kill    | Termination failed; `detail` explains why    |
| `would-kill`           | dry run | The process would be terminated              |
| `would-skip-protected` | dry run | The PID is protected and would be skipped    |

The array is empty when the protected process hierarchy cannot be inspected; the exit code is `1`.

## `agent-files`
### `list`
An array with one entry per configured tool.

| Field               | Type    | Meaning                                              |
| :------------------ | :------ | :--------------------------------------------------- |
| `tool`              | string  | Tool name                                            |
| `command`           | string  | Executable name                                      |
| `available`         | boolean | The executable was found                             |
| `executable`        | string  | Resolved path, or `not found`                        |
| `version`           | string  | First line of `--version`, `unknown`, or `not found` |
| `instructions_file` | string  | Global instructions file                             |
| `skills_dir`        | string  | Skills directory, or `n/a` when the tool has none    |

### `sync` and `check`
An array with one entry per selected tool; also for `sync --dry-run`.

| Field     | Type          | Meaning                                               |
| :-------- | :------------ | :---------------------------------------------------- |
| `tool`    | string        | Tool name                                             |
| `status`  | string        | See the table below                                   |
| `changes` | array[string] | Applied or planned instruction-file and skill changes |

| Status            | Meaning                                                             |
| :---------------- | :------------------------------------------------------------------ |
| `up-to-date`      | Nothing to change                                                   |
| `synced`          | `sync` applied the listed changes                                   |
| `changes-pending` | `check` or `sync --dry-run` found the listed changes                |
| `failed`          | A write or deletion failed; the failure is the last `changes` entry |
| `unavailable`     | A target file cannot be read or has invalid guarded-block markers   |

```json
[
  {"tool": "claude-code", "status": "synced", "changes": ["instructions file updated: ~/.claude/CLAUDE.md"]}
]
```

## `agent-digest`
### `generate`
One object; `generate --dry-run` reports the same statuses and writes nothing.

| Field     | Type          | Meaning                                                |
| :-------- | :------------ | :----------------------------------------------------- |
| `ok`      | boolean       | `true` when the digest was generated within its budget |
| `dry_run` | boolean       | The run wrote nothing                                  |
| `digest`  | object, null  | Digest file; `null` when generation stopped early      |
| `skills`  | array[object] | One entry per derived skill                            |
| `issues`  | array[object] | Problems found; empty when `ok` is `true`              |

### `check`
One object with the same `ok`, `digest`, `skills`, and `issues` fields, and no `dry_run`.
`digest` and `skills` are `null` and `[]` when front-matter fails to parse.
The exit code is `1` when `ok` is `false`.

### Shared Objects
`digest` object:

| Field       | Type    | Meaning                              |
| :---------- | :------ | :----------------------------------- |
| `path`      | string  | Digest file path                     |
| `status`    | string  | File status                          |
| `bytes`     | integer | Size of the expected digest in bytes |
| `max_bytes` | integer | Size budget                          |

`skills` entry:

| Field    | Type          | Meaning                                           |
| :------- | :------------ | :------------------------------------------------ |
| `name`   | string        | Skill name                                        |
| `path`   | string        | `SKILL.md` path                                   |
| `status` | string        | File status                                       |
| `files`  | array[object] | Copied reference files, each `{"path", "status"}` |

`issues` entry:

| Field     | Type         | Meaning                                 |
| :-------- | :----------- | :-------------------------------------- |
| `check`   | string       | Check that failed                       |
| `path`    | string, null | Affected file; `null` when none applies |
| `message` | string       | First line of the error message         |

| Command    | `status` values                   |
| :--------- | :-------------------------------- |
| `generate` | `created`, `updated`, `unchanged` |
| `check`    | `up-to-date`, `missing`, `stale`  |

| Command    | `check` values                                                                                         |
| :--------- | :----------------------------------------------------------------------------------------------------- |
| `generate` | `frontmatter`, `missing-reference`, `digest-size`                                                      |
| `check`    | `frontmatter`, `skill-index`, `missing-skill`, `stale-skill`, `missing-skill-file`, `stale-skill-file` |
| `check`    | `escaping-link`, `missing-digest`, `stale-digest`, `word-budget`, `relative-link`                      |

```json
{
  "ok": true,
  "dry_run": false,
  "digest": {"path": "agent-digest.md", "status": "updated", "bytes": 9120, "max_bytes": 12288},
  "skills": [
    {"name": "python-guidelines", "path": "agent-skills/python-guidelines/SKILL.md", "status": "created", "files": []}
  ],
  "issues": []
}
```

## `lint-markdown`
### `check`
| Field           | Type          | Meaning                                   |
| :-------------- | :------------ | :---------------------------------------- |
| `files_checked` | integer       | Number of Markdown files linted           |
| `issues`        | array[object] | Issues found; the exit code is `1` if any |

Issue object, shared by `check` and `fix`:

| Field       | Type    | Meaning                                                    |
| :---------- | :------ | :--------------------------------------------------------- |
| `path`      | string  | File path, relative to the current directory when possible |
| `line`      | integer | 1-based line number                                        |
| `column`    | integer | 1-based column number                                      |
| `rule_id`   | string  | Rule ID, such as `MD017`                                   |
| `rule_name` | string  | Rule name, such as `aligned-tables`                        |
| `message`   | string  | Problem description                                        |
| `fixable`   | boolean | `fix` can repair the issue                                 |

### `fix`
`fix --dry-run` reports the same fields and writes nothing.

| Field           | Type          | Meaning                                                       |
| :-------------- | :------------ | :------------------------------------------------------------ |
| `dry_run`       | boolean       | The run wrote nothing                                         |
| `files_checked` | integer       | Number of Markdown files linted                               |
| `fixed`         | array[object] | Files that changed: `{"path": string, "fixes": array[issue]}` |
| `issues`        | array[object] | Issues that remain after fixing; the exit code is `1` if any  |

### `rules`
`{"rules": [...]}` with one entry per registered rule.

| Field     | Type    | Meaning                                          |
| :-------- | :------ | :----------------------------------------------- |
| `id`      | string  | Rule ID                                          |
| `name`    | string  | Rule name                                        |
| `scope`   | string  | Rule scope, such as `prose` or `heading`         |
| `fixable` | boolean | `fix` can repair the rule's issues               |
| `enabled` | boolean | The active profile enables the rule              |
| `source`  | string  | `builtin` or the plugin entry that registered it |

```json
{
  "files_checked": 12,
  "issues": [
    {"path": "docs/a.md", "line": 4, "column": 1, "rule_id": "MD017", "rule_name": "aligned-tables", "message": "Table is not aligned.", "fixable": true}
  ]
}
```

## `git-repository-backup`
### `list`
An array with one entry per discovered repository.

| Field  | Type   | Meaning                       |
| :----- | :----- | :---------------------------- |
| `name` | string | Backup name of the repository |
| `path` | string | Repository path               |

### `backup`
An array with one entry per repository and enabled layer; also for `backup --dry-run`.

| Field        | Type   | Meaning                                    |
| :----------- | :----- | :----------------------------------------- |
| `repository` | string | Backup name of the repository              |
| `layer`      | string | `mirror` or `archive`                      |
| `status`     | string | See the table below                        |
| `detail`     | string | Reason; present for `failed` and `skipped` |

| Status          | Layer               | Meaning                                       |
| :-------------- | :------------------ | :-------------------------------------------- |
| `mirrored`      | `mirror`            | The mirror was updated                        |
| `archived`      | `archive`           | The archive was written                       |
| `up-to-date`    | `archive`           | The refs are unchanged since the last archive |
| `would-mirror`  | `mirror`            | Dry run: the mirror would be updated          |
| `would-archive` | `archive`           | Dry run: the archive would be written         |
| `skipped`       | `mirror`, `archive` | The repository has no commits                 |
| `failed`        | `mirror`, `archive` | The layer failed; `detail` explains why       |

### `restore`
One object, printed once the source and target are resolved.

| Field    | Type         | Meaning                                            |
| :------- | :----------- | :------------------------------------------------- |
| `status` | string       | `restored`, `would-restore`, or `failed`           |
| `kind`   | string       | Source kind: `mirror` or `archive`                 |
| `source` | string       | Source path                                        |
| `target` | string       | Target directory                                   |
| `branch` | string, null | Checked-out branch; `null` when none was restored  |
| `detail` | string       | Failure message; present for some `failed` results |

```json
{"status": "restored", "kind": "mirror", "source": "D:/backups/app.git", "target": "C:/restore/app", "branch": "main"}
```

## `config` Command Group
`agent-files`, `lint-markdown`, and `git-repository-backup` share `config`.
`processes` and `agent-digest` have no `config` command.

### `config list`
`{"settings": [entry, ...]}`

### `config get NAME`
One `entry` object.

| Field         | Type    | Meaning                                                                |
| :------------ | :------ | :--------------------------------------------------------------------- |
| `name`        | string  | Setting name                                                           |
| `value`       | any     | Resolved value; `"***"` for a secret that is set                       |
| `source`      | string  | `cli`, `env`, `project`, `user`, `system`, or `default`                |
| `type`        | string  | `string`, `integer`, `float`, `boolean`, `duration`, `list`, or `dict` |
| `default`     | any     | Built-in default; `"***"` for a secret default                         |
| `description` | string  | Setting description                                                    |
| `secret`      | boolean | The value is masked                                                    |

### `config names`
`{"names": [{"name", "type", "default", "description"}, ...]}`

### `config path`
`{"path": string}` for one file.
With `--all`, an object from tier to path: `project`, `user`, and `system`, limited to the tiers the tool supports.
With `--config PATH`, the `--all` object is `{"config": string}`.
