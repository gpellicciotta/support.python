### Evidence
- `default_config_path` in `src/support_python/tools/git_repository_backup.py` returns `~/.config/git-repository-backup/config.json` on every platform.
- `legacy_config_path` returns `~/.config/backup-git-repos/config.json`; `load_config` reads it with a `WARN` when the default is absent.
- `describe_config` reports the config file in the startup banner, marking `(default)`, `(legacy)`, or `(default, absent)`.
- The [Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md#configuration-files) place user files through `XDG_CONFIG_HOME`, then `%APPDATA%` on Windows.
  They also require reading a renamed file's old location with a deprecation warning until the next major version.
- T0058 adds `user_config_path` to `support_python.env`.

### Required Behavior
- `default_config_path()` returns `user_config_path("git-repository-backup")`.
- Discovery without `--config` reads the first existing file of:
  1. `user_config_path("git-repository-backup")`.
  2. `~/.config/git-repository-backup/config.json`, when it differs from item 1, with a `WARN` naming both paths.
  3. `~/.config/backup-git-repos/config.json`, with the existing legacy `WARN`.
- Both old locations stay readable until v3.0.0; the warnings say so.
- `describe_config` marks item 2 as `(old location)` and keeps the other markers.
- `--config PATH` keeps replacing discovery, unchanged.
- On Linux and macOS without `XDG_CONFIG_HOME`, items 1 and 2 coincide, so behavior is unchanged there.

### Tests
- Unit: with `XDG_CONFIG_HOME` set to a temp directory, `default_config_path()` returns `{{tmp}}/git-repository-backup/config.json`.
- Unit: when only the old `~/.config` file exists and differs from the new path, `load_config(None)` reads it and warns once naming both paths.
- Unit: when the new file exists, `load_config(None)` reads it without a warning, even if old files exist.
- Unit: the legacy `backup-git-repos` fallback keeps its current warning.
- Unit: `describe_config(None)` reports `(old location)` for item 2.
- Integration: installed `git-repository-backup list --verbose` with `XDG_CONFIG_HOME` pointing at a temp config shows that file in the startup banner.

### Declared Files
- src/support_python/tools/git_repository_backup.py
- tests/tools/test_git_repository_backup.py
- docs/tools/git-repository-backup.md
- CHANGELOG.md

Completion check: `.venv/Scripts/python -m pytest -q`, `.venv/Scripts/ruff check .`, plus the integration check above.
Size estimate: 4 files, 160 lines.
