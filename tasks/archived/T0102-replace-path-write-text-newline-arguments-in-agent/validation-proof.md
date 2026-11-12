## Walkthrough & Validation

Red phase, GitHub CI run 42862112611 (Python 3.9):
```text
build (3.9, ubuntu-24.04) | 18 failed, 1185 passed, 7 skipped in 55.85s
exit=1
```

Red phase locally, guard test:
```text
$ .venv/Scripts/python -m pytest -q tests/test_python39_compat.py
E       AssertionError: Lists differ: ['tools/agent_digest.py:919', 'tools/agent_digest.py:895'] != []
E       First list contains 2 additional elements.
E       'tools/agent_digest.py:919'
E       - ['tools/agent_digest.py:919', 'tools/agent_digest.py:895']
tests\test_python39_compat.py:26: AssertionError
exit=1
```

Green phase locally:
```text
$ python scripts/devops.py check
All checks passed!
1208 passed, 3 skipped, 191 subtests passed in 143.98s (0:02:23)
Successfully built support_python-2.0.8rc0.tar.gz and support_python-2.0.8rc0-py3-none-any.whl
exit=0
```

Green phase, GitHub CI run 42863145089 on 9a87805:
```text
build (3.9, ubuntu-24.04) | Successfully built support-python
build (3.9, ubuntu-24.04) | All checks passed!
build (3.9, ubuntu-24.04) | 1204 passed, 7 skipped in 52.64s
build (3.9, ubuntu-24.04) | Successfully built support_python-2.0.8rc0.tar.gz and support_python-2.0.8rc0-py3-none-any.whl
build (3.x, ubuntu-latest) | Successfully built support-python
build (3.x, ubuntu-latest) | All checks passed!
build (3.x, ubuntu-latest) | 1204 passed, 7 skipped, 191 subtests passed in 33.51s
build (3.x, ubuntu-latest) | Successfully built support_python-2.0.8rc0.tar.gz and support_python-2.0.8rc0-py3-none-any.whl
exit=0
```
