<!-- BEGIN plan (managed by plan init) -->
This project tracks its work with plan in `PLAN.md` and `.plan/tasks/`.
Load the `plan-task-usage-guidelines` skill before creating, starting, or changing tasks.
Change `PLAN.md` and task frontmatter only through `plan` commands.
<!-- END plan -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`support-python` is a general-purpose Python support library and CLI for Python clients and ops scripts. It aims to have as few
third-party dependencies as possible so downstream consumers aren't burdened by transitive dependencies.
Currently it provides guideline-compliant CLI logging (`CliLogger`/`LogLevel`), a shared CLI version/help
argparse helper (`build_action_parser`/`print_version`/`print_help`), a stdlib-only REST-client HTTP
transport (`Transport`/`UrllibTransport`/`RawResponse`/`TransportError`/`build_query_string`), and a narrow
devops-script step runner (`run_step`); further modules are meant to be pulled out of hand-duplicated
code as shared-library candidates are reviewed and approved (see `PLAN.md`).

## Commands

All commands use the project's venv (`.venv`, created via `python -m venv .venv` — or run
`python scripts/bootstrap-dev-environment.py` for a one-shot bootstrap: creates the venv, installs editable +
dev extras, lints, tests, builds sdist/wheel).

- Install in editable mode, with the `dev` extra (pytest, ruff, build):
  `.venv\Scripts\pip install -e ".[dev]"`
- Lint: `.venv\Scripts\ruff check .` / `.venv\Scripts\ruff format --check .`
- Run the test suite: `.venv\Scripts\python -m pytest` (or `python -m unittest discover -s tests`)
- Run the demo CLI: `.venv\Scripts\support-python greet <name>` (once installed), or
  `python -m support_python.cli greet <name>`.

Dependencies are declared once, in `pyproject.toml` — there is no separate `requirements.txt` to keep in sync.

## Architecture

Modules under `src/support_python/` (public symbols are re-exported from the package root):

- `logging.py`: `LogLevel`, `format_severity_indicator`/`format_log_message`, and `CliLogger` —
  guideline-compliant CLI logging, API-similar to the logging package in support.java.
- `cli.py`: `build_action_parser`/`print_version`/`print_help` — shared argparse helper for action-oriented
  CLIs. `main` (the `support-python` entry point, `greet`/`version`/`help` actions) is a reference
  implementation for downstream consumers.
- `net.py`: stdlib-only REST-client transport (`Transport`, `UrllibTransport`, `RawResponse`,
  `TransportError`, `build_query_string`) and `is_port_in_use`. A non-2xx response is a normal `RawResponse`.
- `errors.py`: REST-client exception hierarchy and status-code mapping helpers.
- `devops.py`: `run_step` plus Docker, MySQL, mail, server, and Cloud SQL proxy managers for local ops scripts.
  Pin it via a consumer's own `scripts/requirements.txt`, never from a bootstrap script
  (see `docs/adrs/ADR-0001-devops-scripts-toolkit-scope.md`).
- `capture.py`, `httpd.py`: headless-Chrome view capture and the embedded static HTTP server.
- `sql.py`: streaming SQL snapshot anonymizer. `crypto.py`: password hashing and property decryption.
- `dates.py`, `models.py`, `tables.py`, `tokens.py`, `env.py`, `terminal.py`, `version.py`: wire dates and
  models, table rendering, token storage, env-file parsing, UTF-8 console setup, and project version lookup.

## Development Guidelines

This repository follows the cross-project
[Development Guidelines](https://github.com/gpellicciotta/dev-guidelines):

- Use semver (`MAJOR.MINOR.PATCH`), currently pre-1.0 (`0.x.y`), so breaking changes are still expected early
  on but must be called out explicitly in `CHANGELOG.md` rather than reading as routine.
- Favour simplicity over ingenuity. Keep things as simple as possible for what's actually needed today — don't
  design for hypothetical future requirements.
- Minimize third-party dependencies. Reach for the standard library first; add a dependency only when it earns
  its ongoing maintenance cost.
- Make it easy to get started: a clone + `python scripts/bootstrap-dev-environment.py` (or the commands under
  Commands above) should be enough to get a working venv, passing tests, and a build — no undocumented setup
  steps.
- Use the same tools and techniques the rest of the Python ecosystem is using (src-layout, `pyproject.toml`,
  pytest, ruff, GitHub Actions) unless there's a concrete reason to deviate.
- CLI design: prefer action-oriented, subcommand-based CLIs (`tool action [options]`). Provide `help` action /
  `-h` / `--help`, `version` action / `--version`, `--verbose` option, and standardized `{name} v{version} -
  {copyright}` header with exit codes.

## Conventions

- `CHANGELOG.md` (top-level) tracks version history; the top heading carries a `-pre` SemVer suffix while
  under active development (e.g. `## v0.1.1-pre`), replaced with a status tag (`[YYYY-MM-DD]` /
  `[released: YYYY-MM-DD]` / `[broken]`) at freeze/release time. `pyproject.toml`'s `version` must always
  match the top heading exactly, `-pre` included.
- `PLAN.md` and `.plan/tasks/` track tasks; change them only through `plan` commands.
- Mandatory docs: `docs/index.md`, `docs/requirements.md`, and `docs/devops.md`.
- Keep `README.md`'s build/install/usage sections in sync with the code as it evolves — treat drift there as a
  bug, not a documentation nice-to-have.
- Style guide: spaces for indentation (never tabs), 4-space indent width, 132-character line length, UTF-8
  everywhere. Enforced by `.editorconfig` (editor-level) and `ruff` (`pyproject.toml`'s `[tool.ruff]`, run via
  `ruff check .` / `ruff format --check .`, wired into CI) — don't let either drift from these numbers.
