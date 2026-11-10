---
task: T0033
round: 2
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T01:59:07Z
reviewed_commit: "04f32c0"
base_commit: "3db050a"
branch: task/T0033-let-lint-markdown-load-extra-rules-from-plugin
---
# Review Findings: Task T0033 (Round 2)

## Summary
Approved: commit `04f32c0` fixes all three round-1 defects, and each fix has a regression test.
- `build_linter` passes one `loaded` set to both `load_plugins` calls, so a plugin listed in both sources loads once.
- `run_rules` now looks up sources by `rule.rule_id.strip().upper()`, which matches the keys `load_plugins` returns.
- `resolve_config_file` turns a directory `--config` into its config file before plugins load; `load_profile` reuses it.

Verification I ran on `04f32c0` with `PYTHONPATH=src` and the main checkout's venv:
- `python -m pytest -q`: 776 passed, 3 skipped, 81 subtests passed, exit 0.
- `ruff check .` and `ruff format --check .`: clean, 132 files formatted.
- Manual CLI runs in a temporary project:
  - Plugin in config and `--plugin`: X001 reported once, exit 1.
  - `--config ..` from a subdirectory: X001 reported, exit 1.
  - A lowercase `x002` rule: `rules` lists source `lower.py`.
  - An invalid `plugins` value: exit 2.
- `lint-markdown check --offline` on changed docs: every finding is on a line this branch did not touch.

## Defects
None.

Non-blocking observations:
- Naming one file as a module (`rules.no_todo`) and as a path (`rules/no_todo.py`) exits 2 with a collision.
  - These are two import identities, and the error names the plugin, so this behavior is acceptable.
- The untouched `--rules` doc line still says `MD0xx` codes, but plugin IDs such as `X001` work too.

## Process Gaps
None.
The red-phase and green-phase evidence for the rework is in `validation-proof.md`.
The Execution Log records the rework and updated outcomes, and the commit message follows the guidelines.
The undeclared `CLAUDE.md` edit was already noted in the Execution Log.

## Required Rework
None.
