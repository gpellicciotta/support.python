# Specification: `git-repository-backup` Config File

Configuration file format of `git-repository-backup`.
Implemented in [git_repository_backup.py](../../src/support_python/tools/git_repository_backup.py).
Usage is in [git-repository-backup.md](../tools/git-repository-backup.md).

---

## Files and Precedence
Each setting takes the first valid value from these sources:
1. The command-line option.
2. The environment variable `GIT_REPOSITORY_BACKUP_{{NAME}}`, such as `GIT_REPOSITORY_BACKUP_MIRROR_DIR`.
3. The user file `{{user-config-dir}}/git-repository-backup/config.json`.
4. The system file `%PROGRAMDATA%/git-repository-backup/config.json` on Windows, `/etc/git-repository-backup/config.json` elsewhere.
5. The built-in default.

- The tool has no project file.
- `--config PATH` replaces both files.
- `{{user-config-dir}}` is `$XDG_CONFIG_HOME` when absolute, else `%APPDATA%` on Windows, else `~/.config`.
- Two older user files stand in for an absent user file, each with a warning until v3.0.0:
  `~/.config/git-repository-backup/config.json` and `~/.config/backup-git-repos/config.json`.
- `config set` and `config delete` write the user file, or the system file with `--system`.

## File Shape
- The file holds one UTF-8 JSON object.
- Keys use `kebab-case`; `snake_case` spellings are accepted.
- Unknown keys are ignored and listed at debug level.
- A malformed file, a non-object file, or a wrongly typed value warns and falls through to the next source.
- List environment values take comma-separated items or a JSON array.

## Settings
| Key                | Type    | Default            | Meaning                                                   |
| :----------------- | :------ | :----------------- | :-------------------------------------------------------- |
| `roots`            | list    | `[]`               | Directories scanned for Git repositories                  |
| `mirror-dir`       | string  | none               | Directory holding one bare mirror per project             |
| `archive-dir`      | string  | none               | Directory holding one encrypted 7-Zip archive per project |
| `depth`            | integer | `2`                | Maximum scan depth below each root                        |
| `seven-zip`        | string  | `7z`, `7zz`, `7za` | 7-Zip executable, found on `PATH` when unset              |
| `password-env`     | string  | none               | Environment variable holding the archive password         |
| `password-keyring` | string  | none               | OS keyring service holding the archive password           |

- Set at most one of `password-env` and `password-keyring`.
- Enable a backup layer by setting its directory: `mirror-dir` for mirrors, `archive-dir` for archives.
- Store the password in the keyring with `set-password`; never write it into the file.

## Example
```json
{
  "roots": ["~/projects", "~/work"],
  "mirror-dir": "//server/backups/git-mirrors",
  "archive-dir": "//server/backups/git-archives",
  "depth": 2,
  "seven-zip": "C:/Program Files/7-Zip/7z.exe",
  "password-keyring": "git-repository-backup"
}
```
