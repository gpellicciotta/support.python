# T0006 Validation Proof

## Locking tests
Command: `python -m pytest tests/test_locking.py -q`

```text
...............                                                          [100%]
15 passed in 1.17s
```

## Full suite
Command: `python -m pytest -v -x --ignore=tests/test_locking.py`

```text
============= 428 passed, 50 subtests passed in 68.01s (0:01:08) =============
```

## Lint and format
Commands: `ruff check .` and `ruff format --check .`

```text
All checks passed!
66 files already formatted
```

## Notes
- Tests and implementation were authored together; a failing-first run was not recorded.
