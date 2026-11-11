# Validation Proof

## Red phase
Command: `python -m pytest tests/tools/test_processes.py -q -k "yes or confirmation or never_asks"`
```
FAILED test_processes_kill_yes_flag_skips_confirmation
FAILED test_processes_kill_typed_confirmation_on_a_terminal
FAILED test_processes_kill_without_yes_fails_when_stdin_is_not_a_terminal  (assert (0 == 2))
3 failed, 1 passed in 2.52s
```

## Green phase
```
python -m pytest -q                      -> 1130 passed, 5 skipped, 181 subtests passed in 10.79s
PYTHONPATH=src python -m pytest -m slow --timeout=120 tests/tools/test_processes.py -q -n0 -> 3 passed, 10 deselected in 4.41s
ruff check src tests                     -> All checks passed!
ruff format --check src tests            -> 130 files already formatted
lint-markdown check --offline (3 docs)   -> All 3 markdown files passed linting.
```
Note: the worktree has no `.venv`, and the main `.venv` console scripts cannot import the worktree package, so slow tests ran with `PYTHONPATH=src`.
