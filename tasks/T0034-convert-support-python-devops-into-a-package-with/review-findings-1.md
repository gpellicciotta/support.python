---
task: T0034
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T19:50:01Z
reviewed_commit: "5a6bd59"
base_commit: "886c224"
branch: task/T0034-convert-support-python-devops-into-a-package-with
---
# Review Findings: Task T0034 (Round 1)

## Summary
The split itself is correct and behavior-preserving.
It is rejected only because the changelog hides a verified downstream break.

Verified independently:
- An AST comparison of `main:src/support_python/devops.py` against `steps.py` and `services.py` showed every top-level definition byte-identical.
  No definitions are missing, duplicated, or new apart from the per-module `__all__` lists.
- `devops/__init__.py` re-exports exactly the 12 pre-split `__all__` names.
  `support_python` root re-exports resolve to the same objects.
- Git records `devops.py` as renamed to `devops/services.py`, matching the spec's `git mv` instruction.
- `.venv/Scripts/python -m pytest -q`: 735 passed, 3 skipped, 64 subtests passed.
- `ruff check .` and `ruff format --check .`: clean (100 files).
- `PYTHONPATH=src python ../auth/scripts/devops.py --help` exits 0 and loads the worktree's `devops/__init__.py`.
- The red-phase proof in `validation-proof.md` shows the expected `ImportError` before the split.
- Single-sentence commit message, no trailers, within 20 words.
- `pyproject.toml` relies on setuptools auto-discovery, so the new subpackage ships the same way `support_python.markdown` does.

## Defects
1. **Undocumented breaking change for downstream test suites (CHANGELOG.md).**
   Module-level names such as `support_python.devops.is_port_in_use`, `.signal`, and `.subprocess` no longer exist on the package.
   `patch("support_python.devops.is_port_in_use")` now raises `AttributeError`; I reproduced this against the worktree.
   Two sibling consumers patch these exact targets:
   - `counters.server/clients/python/tests/test_devops.py` (lines 184, 186, 213: `devops.signal.signal`, `devops.is_port_in_use`).
   - `todos.server/scripts/tests/test-local-server-command.py` (lines 41, 42, 102, 127, 147).
   Re-exporting `is_port_in_use` would not help, because the patch would no longer reach the binding `services.py` uses.
   CLAUDE.md requires an explicit `**[breaking]**` CHANGELOG note for backward-incompatible changes.
   ADR-0003 also classifies restructuring `support_python.devops` as backward-incompatible.
   The new entry is tagged `DevEx` and states only that public re-exports were preserved, so it reads as non-breaking.

## Process Gaps
- No task captured the downstream impact on the sibling consumers.
  CLAUDE.md permits recording such findings with `plan tasks create --project {{path}} --backlog`.
- The integration check covered only `auth/scripts/devops.py --help`, which exercises imports but not consumer test suites.
  A repository-wide search for `support_python.devops.` patch targets would have found both breakages.

## Required Rework
1. Mark the CHANGELOG entry `**[breaking]**`.
   Say that mock patch targets moved from `support_python.devops.<name>` to `support_python.devops.steps.<name>` or `support_python.devops.services.<name>`.
   Give `support_python.devops.services.is_port_in_use` and `support_python.devops.services.signal.signal` as examples.
2. Record backlog tasks for `counters.server` and `todos.server` to update those patch targets when they adopt v2.
   Add an Execution Log entry that references those tasks.
