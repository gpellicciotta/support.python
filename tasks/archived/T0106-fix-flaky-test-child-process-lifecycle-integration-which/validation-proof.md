## Walkthrough & Validation

### Failing test before the change
The flake was not reproduced; it failed once under xdist load. Suspected cause: a single `taskkill` call with a 5 second timeout.

### Tests after the change
```text
$ python -m pytest tests/test_processes.py -q -p no:cacheprovider
............................                                             [100%]
28 passed in 3.16s
$ python -m pytest -q -p no:cacheprovider
1219 passed, 5 skipped, 181 subtests passed in 15.42s
$ python -m ruff check src tests
All checks passed!
```

### Integration scenario
The full suite ran under xdist, which is the load condition that caused the original failure.
