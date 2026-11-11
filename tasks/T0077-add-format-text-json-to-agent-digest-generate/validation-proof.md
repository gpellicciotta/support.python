# Validation Proof T0077

## Red phase
`python -m pytest tests/tools/test_agent_digest.py -k GenerateJson -q` before implementation: `7 failed, 1 passed` (JSONDecodeError, stdout empty; the exit-2 test passed via argparse rejecting `--format`).

## Green phase
- `python -m pytest tests -q -x`: `1142 passed, 5 skipped, 181 subtests passed`
- `python -m pytest -m slow --timeout=120 tests/tools/test_agent_digest.py -q`: `4 passed`
- `ruff check src tests`: `All checks passed!`; `ruff format` applied.
- `lint-markdown check --offline`: only 7 pre-existing issues in frozen `tests/fixtures/agent_digest/`.
- `scripts/devops.py check` not run: the worktree has no `.venv`; ran pytest and ruff from the main checkout venv instead.
