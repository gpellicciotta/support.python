---
name: python-guidelines
description: >-
  Guidelines and conventions for Python code, src/ layout, pyproject.toml
  configuration, pytest, Ruff linting, and persistence. Use when writing, editing,
  or testing Python code or scripts.
---

# Python Guidelines
Guidelines on writing Python code and structuring Python projects.

## Starting Projects
- Start Python projects from [template.python](https://github.com/gpellicciotta/template.python.git).

## Ecosystem Compliance
- Use established Python ecosystem practices unless a concrete documented reason justifies deviation.

## Packaging and Project Structure
- Use a `src/` layout to prevent accidental imports from the repository root during testing.
- Use valid Python identifiers with underscores for package and module directories (e.g. `src/mail_utils/`).
- Name directly executed standalone scripts using lowercase with dashes (`kebab-case`, e.g. `scripts/run-checks.py`).
- Name pytest test modules using snake_case with the `test_` prefix (e.g. `tests/test_parser.py`).
- Use `pyproject.toml` as the single source of truth for metadata, dependencies, and build configuration.
- Resolve version numbers dynamically at runtime via `importlib.metadata.version(...)` rather than hardcoding version strings.
- Produce standard source distributions and wheels, and validate package building in CI.
- Keep console scripts and public entry points stable, documented, and covered by tests.
- Document module boundaries and single responsibilities in package `__init__.py` and top-level docstrings.

## Code Style and Documentation
- Document all public API surface with docstrings, including modules, classes, functions, methods, attributes, and enum members.
- Avoid splitting signatures or call invocations across multiple lines when they fit within standard line limits.
- Indent continuation lines when splitting signatures or invocations, placing one argument or parameter per line.

## Supported Versions and Dependencies
- Keep supported Python versions consistent across `requires-python`, CI, setup documentation, and package metadata.

## Testing and Quality
- Use pytest for unit, command-line, and integration tests.
- Run linting and formatting checks in CI with `ruff check` and `ruff format --check`.
- Use anonymized, committed fixtures for stable integration coverage of complex file formats or real-world inputs.

## Configuration and Persistence
- Centralize configuration and filesystem paths using `pathlib`.
- Document and test deliberate capability limits rather than leaving them as implicit implementation details.

## Portability
- Use platform-neutral standard-library APIs where practical.
- Isolate platform-specific scheduling, shell commands, and filesystem behavior behind testable functions.
