# Git Repository Backup

Dual-layer Git repository backup and restore utility implemented in [git_repository_backup.py](../../src/support_python/tools/git_repository_backup.py) and exposed on the command line as `git-repository-backup`.

---

## Command-Line Interface
Run actions through the `git-repository-backup` console script in [git_repository_backup.py](../../src/support_python/tools/git_repository_backup.py):
```bash
git-repository-backup backup [options]
git-repository-backup list [--format text|json] [options]
git-repository-backup restore (--source PATH | --name NAME) --target DIR [options]
git-repository-backup set-password --archive-dir PATH --password-keyring NAME [options]
```

Supported options:
- `--config PATH` loads explicit JSON settings from `PATH`.
- `--root PATH` adds a directory to scan for repositories (repeatable; overrides `roots` in config).
- `--depth N` sets the maximum scan depth below each root (default: `2`).
- `--mirror-dir PATH` sets the directory holding bare mirror repositories (`{{name}}.git`).
- `--no-mirror` disables the mirror backup layer.
- `--archive-dir PATH` sets the directory holding AES-256 encrypted 7-Zip archives (`{{name}}.7z`).
- `--no-archive` disables the archive backup layer.
- `--format text|json` selects human-readable lines (`{{name}}  {{path}}`) or a JSON array of `{"name": "...", "path": "..."}` objects for `list` (default: `text`).
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
Config resolution checks locations in priority order:
- Explicit `--config PATH` (must exist), which replaces the discovery below.
- The user config file, when present, from [user_config_path](../../src/support_python/env.py):
  `$XDG_CONFIG_HOME/git-repository-backup/config.json` when `XDG_CONFIG_HOME` is an absolute path,
  else `%APPDATA%/git-repository-backup/config.json` on Windows or `~/.config/git-repository-backup/config.json` elsewhere.
- The old `~/.config/git-repository-backup/config.json`, when it differs from the user config file and is present.
  It emits a `WARN` notice on `stderr` (support ends in `v3.0.0`).
- Legacy `~/.config/backup-git-repos/config.json` when present, emitting a `WARN` notice on `stderr` (support ends in `v3.0.0`).
- Command-line flags only when no default file exists.

The startup banner marks the file it read as `(default)`, `(old location)`, or `(legacy)`, or shows `(default, absent)`.

Config keys accept dashes or underscores interchangeably; kebab-case is preferred.

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

| Field              | Type            | Default       | Purpose                                              |
| :----------------- | :-------------- | :------------ | :--------------------------------------------------- |
| `roots`            | `array<string>` | `[]`          | Root directories scanned for Git repositories        |
| `mirror-dir`       | `string`        | `null`        | Target directory for bare mirror repositories        |
| `archive-dir`      | `string`        | `null`        | Target directory for encrypted `.7z` bundle archives |
| `depth`            | `integer`       | `2`           | Maximum directory recursion depth below each root    |
| `seven-zip`        | `string`        | Auto-detected | Path or command name for the 7-Zip executable        |
| `password-env`     | `string`        | `null`        | Environment variable holding the archive password    |
| `password-keyring` | `string`        | `null`        | OS keyring service name holding the archive password |
