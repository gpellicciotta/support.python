---
id: T0080
owner: ~
needs: []
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0080: Document every public symbol in src/ and enforce public docstrings with ruff pydocstyle rules

## Goals
Give every public module, class, function, method, and `__init__` in `src/` a docstring, as the Python guidelines require.
Enable ruff `D100` to `D107` for `src/` in pyproject.toml so CI keeps it that way.
Review existing docstrings in the touched modules for accuracy against current behavior.

## Task Execution Steps
- [ ] **[Read]**      Run `ruff check src --select D1` and record the 70 baseline findings.
- [ ] **[Implement]** Enable `D100`-`D107` for `src/` in pyproject.toml, excluding tests and scripts.
- [ ] **[Verify]**    Run `ruff check .` and record the failures as red-phase proof.
- [ ] **[Implement]** Write docstrings for every flagged symbol, starting with rules.py, projects.py, agent_files.py, and lint.py.
- [ ] **[Verify]**    Run `ruff check .` and the fast suite, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Add a CHANGELOG.md entry.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
