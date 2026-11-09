### Changes
- Keep the capture actions (capture, tour, list, version, help) and options (`--url`/`--path`, `--output`, `--viewport`,
  `--mobile`, `--desktop`, `--mode`, `--all`, `--tour`, `--chrome-path`, `--port`, `--no-server`, `--log-file`, and the rest).
- Help and version output switch to the `ToolHarness` format, with `config.cli_name` and `config.author` in the banner.
- Delete `build_action_parser`, `print_help`, `print_version`, and `format_version` from `cli.py`, `__all__`, and the package root.
- Grep `src`, `tests`, and `scripts` for remaining uses; `scripts/` must keep using only `_cli_common.py`.

### Declared Files
- src/support_python/capture.py
- src/support_python/cli.py
- src/support_python/__init__.py
- tests/test_capture.py
- tests/test_cli.py
- README.md
- CHANGELOG.md

### Tests
- Unit: capture CLI help and version use the harness banner; each action dispatches as before (capture execution mocked).
- Unit: option parsing for `--url`, `--viewport`, `--mobile`, `--all`, and `--tour` yields the same settings as before.
- Unit: `support_python.cli` no longer exposes the four removed helpers.
- Integration: with this checkout's `src` on `PYTHONPATH`, `python ../auth/scripts/capture-view.py help` exits 0
  (read-only use of a sibling consumer); waive with the reason if auth needs unavailable dependencies.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration check above.
Size estimate: 7 files, 350 lines.
