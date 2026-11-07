# T0010 Validation Proof

## Redis Locking Tests
Command: `python -m pytest tests/test_locking.py tests/test_locking_redis.py -q`

```text
..................s                                                      [100%]
18 passed, 1 skipped in 1.34s
```

## Lint and format
Commands: `ruff check .` and `ruff format --check .`

```text
All checks passed!
66 files already formatted
```
