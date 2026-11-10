---
name: cli-guidelines
description: >-
  Conventions for command-line interface design, standard subcommands, flags, exit
  codes, and operational testing. Use when building, refactoring, documenting, or
  testing CLI tools.
---

# CLI Guidelines
Conventions and standards for designing, structuring, documenting, and testing command-line interfaces.

## Subcommand Architecture and Flags
- Design command-line interfaces around action-oriented subcommands.
- Reserve command-line options for modifying subcommand behavior.
- Always provide a `version` subcommand and `--version` option exiting with code 0.
- Output a single line for version requests formatted as `{{name}} v{{version}} - {{copyright}}`.
- Always provide a `help` subcommand and `--help` / `-h` options exiting with code 0.
- Support `help --verbose` to print full documentation across every supported action and subcommand.
- Help screens must include the version header line, description, usage syntax, subcommands, options, and exit codes.
- Support `--log-file` and `--log-level` options on logging tools following the logging guidelines.
- Provide `--verbose` / `-v` and `--debug` shorthand flags on tools supporting operational logs or progressive diagnostics.
- The `--debug` flag is exactly equivalent to passing `--log-level DEBUG`.
- The `--verbose` flag emits progress detail at `INFO` severity without changing the logging threshold.
- Explicit `--log-level` values override `--debug` when both options are supplied.

## Standard Exit Codes Contract
- Return exit code 0 upon successful command execution.
- Return exit code 1 when operational or runtime execution errors occur.
- Return exit code 2 when invalid arguments or syntax errors are supplied.

## Operational Subcommands
- Provide a `versions` subcommand in `devops.py` supporting status inspection, drift checking, and synchronized bumping.
- Provide a `production` subcommand in `devops.py` supporting `deploy`, `check`, `build`, `migrate`, `smoke-test`, and `rollback` actions.
- Support `--dry-run`, `--no-rollback`, and `--no-changelog-commit` options on deployment workflows.
