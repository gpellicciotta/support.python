# T0011 Validation Proof

## MySQL Locking Tests
Command: `python -m pytest tests/test_locking.py tests/test_locking_redis.py tests/test_locking_mysql.py -q`

```text
................s........s                                               [100%]
24 passed, 2 skipped in 1.46s
```

## Lint and format
Commands: `ruff check .` and `ruff format --check .`

```text
All checks passed!
67 files already formatted
```
