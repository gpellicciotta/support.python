## Walkthrough & Validation

Sibling upgrade tasks, each completed with a Codex review and pushed:
- auth T0220 (code f865a7e); T0217 cancelled as folded in.
- counters.server T0269 (4be6137, 74e1915) and T0271 (22884ed); T0266 folded in, stale T0250 cancelled.
- todos.server T0212 (eeb1c17) and T0213 (a1767a6); T0210 folded in.
- template.python T0015, T0014, T0016, T0017 by session support-python-9b (main at 0a59a6f).

Sibling suites against support-python v2.0.0, each in its project-local `.venv`, on 2026-11-10 (all exit 0):
```text
$ (auth) python scripts/bootstrap-dev-environment.py --skip-build && .venv/Scripts/python -m pytest -q scripts/tests
120 passed in 7.46s
$ (auth) PYTHONPATH=clients/python/src .venv/Scripts/python -m pytest -q clients/python/tests
109 passed in 0.73s
$ (todos.server) PYTHONPATH=clients/python/src .venv/Scripts/python -m pytest -q clients/python/tests
270 passed, 16 skipped in 4.83s
$ (counters.server) cd clients/python && ../../.venv/Scripts/python -m pytest -q
80 passed in 3.04s
$ (template.python) .venv/Scripts/python -m pytest -q
28 passed in 1.13s
$ grep -h "support-python" each pin file
"support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0",
support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0
"support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0",
support-python[mysql] @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0
"support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0",
support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0
"support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0",
support-python @ git+https://github.com/gpellicciotta/support.python.git@v2.0.0
```

Gaps the migrations exposed, fixed in support.python:
- `migration-v2.md`: project-local `.venv` installs, and kept names whose output changed (865448c, 4c96102).
- T0095 (DevopsCli description), T0099 (ToolHarness leading options), T0094 (capture option hooks).
