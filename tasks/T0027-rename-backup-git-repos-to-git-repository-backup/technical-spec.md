### Config Resolution
1. `--config PATH` wins, with today's behavior for a missing file.
2. Otherwise, use `~/.config/git-repository-backup/config.json` when it exists.
3. Otherwise, use `~/.config/backup-git-repos/config.json` when it exists, logging one `WARN`:
   `Reading legacy config <path>; move it to <new path>. The legacy path is dropped in v3.0.0.`
4. Otherwise, use command-line options only, as today.
- Tests redirect the home directory (patch `Path.home`, or set `HOME` and `USERPROFILE`) and never touch the real profile.

### list --format
- `text`, the default, keeps today's output.
- `json` prints one JSON array on stdout, one object per backup, with the fields the text output shows as snake_case keys.
- In JSON mode, stdout carries only the JSON document; mirror how `processes list --format json` keeps it parseable.

### Exit Codes
- 0 success, 1 operational failure, 2 invalid arguments; fix any path that diverges.

### Declared Files
- src/support_python/tools/git_repository_backup.py
- tests/tools/test_git_repository_backup.py
- docs/tools/git-repository-backup.md
- docs/index.md
- README.md
- CHANGELOG.md

### Tests
- Unit: banner, usage, and temporary-directory prefixes use `git-repository-backup`.
- Unit: config resolution covers explicit, new, legacy-with-warning, and no config, under a temporary home.
- Unit: `list --format json` emits a parseable JSON array on stdout, and `--format text` output is unchanged.
- Integration: with `HOME` and `USERPROFILE` pointing at a temporary directory holding only a legacy config,
  installed `git-repository-backup list --format json` exits 0, prints JSON, and warns on stderr.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration command above.
Size estimate: 6 files, 350 lines.
