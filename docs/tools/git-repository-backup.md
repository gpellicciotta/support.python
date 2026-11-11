# Git Repository Backup

Dual-layer Git repository backup and restore utility implemented in [git_repository_backup.py](../../src/support_python/tools/git_repository_backup.py) and exposed on the command line as `git-repository-backup`.
Specifications: [config file](../specs/config-git-repository-backup.md) and [JSON output](../specs/json-output.md).

---

## Command-Line Interface
Run actions through the `git-repository-backup` console script in [git_repository_backup.py](../../src/support_python/tools/git_repository_backup.py):
```bash
git-repository-backup backup [--format text|json] [options]
git-repository-backup list [--format text|json] [options]
git-repository-backup restore (--source PATH | --name NAME) --target DIR [--format text|json] [options]
git-repository-backup set-password --archive-dir PATH --password-keyring NAME [options]
git-repository-backup config [list|names|path|get|set|delete|edit] [name] [value] [options]
```

Supported options:
- `--config PATH` loads explicit JSON settings from `PATH`, replacing the user and system files.
- `--root PATH` adds a directory to scan for repositories (repeatable; overrides `roots` in config).
- `--depth N` sets the maximum scan depth below each root (default: `2`).
- `--mirror-dir PATH` sets the directory holding bare mirror repositories (`{{name}}.git`).
- `--no-mirror` disables the mirror backup layer.
- `--archive-dir PATH` sets the directory holding AES-256 encrypted 7-Zip archives (`{{name}}.7z`).
- `--no-archive` disables the archive backup layer.
- `--format text|json` selects text or JSON output on `list`, `backup`, and `restore` (default: `text`); see [JSON Output](#json-output).
- `list` prints `{{name}}  {{path}}` lines in `text` mode, or a JSON array of `{"name": "...", "path": "..."}` objects.
- In `json` mode, log messages go to `stderr` so `stdout` holds only the JSON document.
- `--source PATH` restores from a specific bare mirror directory or `.7z` archive file.
- `--name NAME` restores a named repository from `--mirror-dir` or `--archive-dir` (preferring the mirror).
- `--target DIR` sets the destination directory for `restore` (must be absent or empty).
- `--seven-zip PATH` overrides the 7-Zip executable (`7z`, `7zz`, or `7za`).
- `--password-env NAME` reads the archive password from environment variable `NAME`.
- `--password-keyring NAME` reads or stores the archive password under OS keyring service `NAME`.
- `--dry-run` reports planned operations without writing anything.

Exit codes:
- `0` on success.
- `1` on operational backup, verification, or restore failure.
- `2` on invalid arguments or configuration.
- `130` when interrupted with `Ctrl+C`.

---

## Configuration Discovery and Schema
Each setting takes the first valid value of these sources, highest first:
1. The command-line option.
2. The environment variable `GIT_REPOSITORY_BACKUP_{{NAME}}`, where `{{NAME}}` is the setting name in upper case with dashes as underscores. An empty variable counts as unset.
3. The user config file, from [user_config_path](../../src/support_python/env.py):
   `$XDG_CONFIG_HOME/git-repository-backup/config.json` when `XDG_CONFIG_HOME` is an absolute path,
   else `%APPDATA%/git-repository-backup/config.json` on Windows or `~/.config/git-repository-backup/config.json` elsewhere.
4. The system config file: `%PROGRAMDATA%/git-repository-backup/config.json` on Windows, else `/etc/git-repository-backup/config.json`.
5. The built-in default.

The tool has no project config file. An explicit `--config PATH` must exist and replaces both files.

When the user file is absent, these deprecated files stand in for it, each emitting a `WARN` notice on `stderr` (support ends in `v3.0.0`):
- The old `~/.config/git-repository-backup/config.json`, when it differs from the user config file.
- The legacy `~/.config/backup-git-repos/config.json`.

The startup banner marks the file it read as `(default)`, `(old location)`, or `(legacy)`, or shows `(default, absent)`.

Config keys accept dashes or underscores interchangeably; kebab-case is preferred.
Unknown keys are ignored and listed with `--debug`.
An invalid value, an unreadable file, or malformed JSON warns once on `stderr`, naming the value or file, and is skipped; it no longer exits `2`.
Lists such as `roots` take a JSON array in files, and comma-separated items or a JSON array in environment variables.

```json
{
  "roots": ["~/projects"],
  "mirror-dir": "//server/backups/git",
  "archive-dir": "~/backups/archives",
  "depth": 2,
  "seven-zip": "7z",
  "password-keyring": "git-repository-backup"
}
```

| Setting            | Environment variable                      | Type            | Default       | Purpose                                              |
| :----------------- | :---------------------------------------- | :-------------- | :------------ | :--------------------------------------------------- |
| `roots`            | `GIT_REPOSITORY_BACKUP_ROOTS`             | `array<string>` | `[]`          | Root directories scanned for Git repositories        |
| `mirror-dir`       | `GIT_REPOSITORY_BACKUP_MIRROR_DIR`        | `string`        | `null`        | Target directory for bare mirror repositories        |
| `archive-dir`      | `GIT_REPOSITORY_BACKUP_ARCHIVE_DIR`       | `string`        | `null`        | Target directory for encrypted `.7z` bundle archives |
| `depth`            | `GIT_REPOSITORY_BACKUP_DEPTH`             | `integer`       | `2`           | Maximum directory recursion depth below each root    |
| `seven-zip`        | `GIT_REPOSITORY_BACKUP_SEVEN_ZIP`         | `string`        | Auto-detected | Path or command name for the 7-Zip executable        |
| `password-env`     | `GIT_REPOSITORY_BACKUP_PASSWORD_ENV`      | `string`        | `null`        | Environment variable holding the archive password    |
| `password-keyring` | `GIT_REPOSITORY_BACKUP_PASSWORD_KEYRING`  | `string`        | `null`        | OS keyring service name holding the archive password |

Set at most one of `password-env` and `password-keyring`.
`password-env` names a variable; it does not hold the password, so no setting is secret.

---

## The config Action
`config` inspects and changes settings with the standard sub-actions `list` (the default), `names`, `path`, `get`, `set`, `delete`, and `edit`:
```bash
git-repository-backup config list --verbose
git-repository-backup config get depth --verbose
git-repository-backup config set mirror-dir //server/backups/git
git-repository-backup config set roots ~/projects,~/work --system
git-repository-backup config delete depth
git-repository-backup config path --all
```

- `set`, `delete`, `path`, and `edit` target the user file; add `--system` for the system file.
- `list` and `get` show each effective value with its source: `cli`, `env`, `user`, `system`, or `default`.
- `get --verbose` prints the full setting card; the `--source` flag of `get` is unavailable because `--source` names the restore source.
- `list`, `names`, `path`, and `get` accept `--format text|json`.
- Unknown names and invalid values exit `2` and leave files untouched.
- The action reads only the user and system files; deprecated locations stay read-only for `backup`, `list`, and `restore`.

---

## JSON Output
`backup --format json` prints one JSON array on `stdout` with one entry per repository and enabled layer, for exit codes `0` and `1`:
```json
[
  {"repository": "alpha", "layer": "mirror", "status": "mirrored"},
  {"repository": "alpha", "layer": "archive", "status": "archived"},
  {"repository": "beta", "layer": "mirror", "status": "failed", "detail": "git fetch failed"}
]
```

- `layer` is `mirror` or `archive`.
- `status` is `mirrored`, `archived`, `up-to-date` (archive unchanged), `would-mirror`, `would-archive` (`--dry-run`), `skipped`, or `failed`.
- `detail` holds the reason for `skipped` and `failed` entries.
- Repositories without commits are `skipped`; a failed archive layer setup marks every pending repository `failed`.

`restore --format json` prints one JSON object once the source and target are resolved:
```json
{"status": "restored", "kind": "mirror", "source": "mirrors/alpha.git", "target": "restored/alpha", "branch": "main"}
```

- `status` is `restored`, `would-restore` (`--dry-run`), or `failed`, with the reason in `detail`.
- `kind` is `mirror` or `archive`; `branch` is the checked-out branch, or `null` when none was checked out.
- Log messages go to `stderr`; invalid arguments or configuration (exit `2`) print nothing on `stdout`.
