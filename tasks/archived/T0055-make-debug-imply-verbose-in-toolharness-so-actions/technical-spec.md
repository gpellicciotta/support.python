# Make --debug imply --verbose in ToolHarness

## Technical Specifications
### Evidence
- `CliLogger.__init__` in `src/support_python/logging.py` sets `self.verbose = verbose or debug`.
- `ToolHarness` in `src/support_python/cli.py` passes `args.verbose` through unchanged.
- `help` action help reads `getattr(args, "verbose", False)` in `src/support_python/cli.py`.
- `agent-files review` passes `args.verbose` to `run_review` in `src/support_python/tools/agent_files.py`.
- `lint-markdown` checks `args.verbose` before its clean-run message in `src/support_python/tools/lint_markdown.py`.

### Required Behavior
- `--debug` alone makes `args.verbose` true for every action handler.
- `help --debug` prints the same detailed help as `help --verbose`.
- `--log-level` still decides the threshold when given with `--debug`; `--debug` still implies `--verbose`.
- `--verbose` alone keeps the `INFO` threshold, as today.

### Out of Scope
- Changing what `--verbose` prints in any tool.

### Tests
- Unit: An action handler receives `args.verbose == True` when the command line holds only `--debug`.
- Unit: `help --debug` output equals `help --verbose` output.
- Unit: `--log-level WARN --debug` yields a `WARN` threshold with `verbose` true.
- Integration: `lint-markdown check --debug` on a clean file prints the same success message as `--verbose`.

### Declared Files
- `src/support_python/cli.py`
- `tests/test_cli.py`
- `docs/requirements.md`
- `docs/tools/agent-digest.md`
- `CHANGELOG.md`
