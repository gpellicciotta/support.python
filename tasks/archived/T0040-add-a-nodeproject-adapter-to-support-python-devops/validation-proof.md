## Walkthrough & Validation

### Key Changes
- Added `NodeProject` to `support_python.devops.projects` and exported it from `support_python.devops`.
- Added `tests/test_devops_projects_node.py`; added `NodeProject` to the pinned `__all__` in `tests/test_devops.py`.
- Documented the npm mapping in `README.md` and `CHANGELOG.md`.

Tests ran with the main checkout's venv and the worktree's `src` first on `PYTHONPATH`.

### Red Phase
Command: `PYTHONPATH=src ../../../.venv/Scripts/python -m pytest -q tests/test_devops_projects_node.py` (exit 2, before implementation)

```text
tests\test_devops_projects_node.py:13: in <module>
    from support_python.devops import NodeProject
E   ImportError: cannot import name 'NodeProject' from 'support_python.devops' (C:\Dev-Projects\support.python\.plan\work\T0040-add-a-nodeproject-adapter-to-support-python-devops\src\support_python\devops\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_devops_projects_node.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.50s
```

### Full Suite and Lint
Commands: `python -m pytest -q`, `ruff check .`, `ruff format --check .` (all exit 0)

```text
947 passed, 3 skipped, 105 subtests passed in 120.70s (0:02:00)
All checks passed!
139 files already formatted
```

### Integration: npm check in a temporary project
Node.js v22.14.0 and npm 10.9.2 are installed, so the check ran rather than being waived.
`package.json` defines `lint` and `test` as `node -e "process.exit(0)"`; the test asserts exit 0 and `dist/demo-2.0.1-pre.tgz`.

```text
tests/test_devops_projects_node.py::NodeNpmIntegrationTests::test_check_passes_and_leaves_a_tarball_in_dist PASSED [100%]
====================== 1 passed, 21 deselected in 1.97s =======================
```

### Integration: read-only versions on support.js
Ran `DevopsCli(NodeProject(Path("../support.js"))).run(["versions"])` from the support.python root (exit 0).
`git -C ../support.js status --short` stayed empty afterwards.

```text
Version file: 3.0.1-pre
CHANGELOG.md: 3.0.1-pre
Versions agree.
Finished devops versions in 0.0s with status: succeeded
exit 0
```

### Markdown Lint
`lint-markdown check README.md CHANGELOG.md` reports 10 issues, all on lines this task did not touch.
