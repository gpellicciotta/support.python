### Requirement
The dev-guidelines [Configuration Guidelines](https://github.com/gpellicciotta/dev-guidelines/blob/main/guidelines/configuration-guidelines.md#configuration-files) place the user file at the first location that applies:
1. `$XDG_CONFIG_HOME/{{tool-name}}/config.json`, on any platform, when `XDG_CONFIG_HOME` is set to an absolute path.
2. Windows: `%APPDATA%/{{tool-name}}/config.json`, the roaming application data folder.
3. Other platforms: `~/.config/{{tool-name}}/config.json`.

No shared helper exists; `git-repository-backup` hard-codes `~/.config/{{tool-name}}/config.json` on every platform.

### API
Add to [env.py](../../../src/support_python/env.py), re-exported from the package root:
```python
def user_config_dir(tool_name: str, *, environ: Mapping[str, str] | None = None, platform: str | None = None) -> Path
def user_config_path(
    tool_name: str, filename: str = "config.json", *, environ: Mapping[str, str] | None = None, platform: str | None = None
) -> Path
```
- `environ` defaults to `os.environ`, and `platform` defaults to `sys.platform`; both exist for tests.
- The functions only compute paths; they never create directories or check that files exist.
- An empty or relative `XDG_CONFIG_HOME` counts as unset, as the XDG Base Directory specification requires.
- On Windows (`platform` starting with `win`), an empty, unset, or relative `APPDATA` falls back to `~/AppData/Roaming`.
- An empty `tool_name`, `.`, `..`, or one containing `/`, `\`, or `:`, raises `ValueError`.

### Decisions
- **[Decided]** Put the helpers in `env.py`, whose docstring already covers configuration utilities.
- **[Decided]** Skip a system-file helper; the guidelines need one only "when needed", and no consumer needs it yet.
- **[Decided]** Split adoption into T0059: switching `git-repository-backup` changes CLI behavior on Windows and can merge separately.

### Declared Files
- src/support_python/env.py
- src/support_python/__init__.py
- tests/test_env.py
- docs/tutorials/script-utilities.md
- docs/requirements.md
- CHANGELOG.md

### Tests
- Unit: an absolute `XDG_CONFIG_HOME` wins on both `linux` and `win32`.
- Unit: an empty or relative `XDG_CONFIG_HOME` is ignored.
- Unit: `win32` uses `APPDATA`, and falls back to `~/AppData/Roaming` when `APPDATA` is empty, unset, or relative.
- Unit: `linux` and `darwin` use `~/.config`.
- Unit: `user_config_path` appends `config.json` by default, or the given file name.
- Unit: an empty tool name, `.`, `..`, or one containing `/`, `\`, or `:`, raises `ValueError`.
- Unit: the package root exports both helpers.
- Integration: a subprocess running `python -c` with `XDG_CONFIG_HOME` set to a temp directory prints `{{tmp}}/demo/config.json` from `support_python.user_config_path("demo")`.

Completion check: `.venv/Scripts/python -m pytest -q`, `.venv/Scripts/ruff check .`
Size estimate: 6 files, 180 lines.
