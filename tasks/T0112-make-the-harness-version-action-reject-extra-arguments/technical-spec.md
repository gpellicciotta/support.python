## Technical Specifications

### Behavior
- `version` alone, or `--version`, prints the banner and exits 0, as today.
- `version` followed by a positional argument logs an error and exits 2, like an unknown subcommand.
  - The error names the first extra argument and prints `Usage: {{tool}} version`.
  - When the harness has a `versions` action, it adds `Did you mean: {{tool}} versions {{argument}}?`.
- Options after `version`, and their values, stay ignored.
  `_reorder_leading_options` moves `--log-level DEBUG version` to `version --log-level DEBUG`, so `DEBUG` is no extra argument.
  Reuse the option arity lookup of `_reorder_leading_options` to tell option values from positional arguments.
- `help` keeps its current handling; this task changes only `version`.

**[Decided]** Exit code 2 matches the usage errors of unknown subcommands and parser errors in `ToolHarness.run`.

### Declared Files
- src/support_python/cli.py
- tests/test_cli.py
- docs/tutorials/cli-harness-and-logging.md

### Tests
- Unit: `run(["version", "3.4.0-pre"])` returns 2 and logs an error naming `3.4.0-pre` with the usage line.
- Unit: With a registered `versions` action, the error suggests `versions 3.4.0-pre`; without it, no hint.
- Unit: `run(["version"])`, `run(["--version"])`, and `run(["--log-level", "DEBUG", "version"])` still return 0.
- Integration: A `DevopsCli` run of `version 1.2.3` exits 2 with the `versions` hint and leaves the version file unchanged.

Size estimate: 3 files, 80 lines

Completion check: `.venv/Scripts/python -m pytest tests/test_cli.py tests/test_devops_cli.py -q`, then the full suite.
