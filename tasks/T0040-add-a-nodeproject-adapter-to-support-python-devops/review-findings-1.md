---
task: T0040
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T03:35:11Z
reviewed_commit: "2d25af7"
base_commit: "cbedc7e"
branch: task/T0040-add-a-nodeproject-adapter-to-support-python-devops
---
# Review Findings: Task T0040 (Round 1)

## Summary
Approved. `NodeProject` meets every goal and the technical spec's script mapping.
- It resolves npm through `resolve_executable`.
- lint, format, test, build, check, and clean match the spec table.
- `package.json` versions go through the existing `VERSION_FILES` entry.
- `release_assets` returns the sorted `dist/*.tgz` tarballs.
- `DevopsCli` passes `project.build` as the post-freeze hook, so released tarballs carry the release version.
- A missing script logs `npm script '<name>' is not defined in package.json.` and exits 1.
- Missing npm and a missing or malformed `package.json` both fail cleanly without running commands.
- README.md, CHANGELOG.md, the package docstring, and `__all__` are updated consistently.

Reviewer verification at `2d25af7`, using the main checkout venv with the worktree `src` first on `PYTHONPATH`:
- `python -m pytest -q`: 947 passed, 3 skipped, 105 subtests passed, exit 0.
- `ruff check .` passed, and `ruff format --check .` reported 139 files already formatted.
- `tests/test_devops_projects_node.py` plus `tests/test_devops.py`: 70 passed, including the real-npm `check` integration test (Node.js is installed, so it was not skipped).
- `DevopsCli(NodeProject(Path("../support.js"))).run(["versions"])` exited 0, reporting 3.0.1-pre for both files. `git -C ../support.js status --short` stayed empty.
- The mapping matches `../support.js/scripts/devops.py` and `../todos.webapp/scripts/devops.py` (`npm run lint`, `npm run format`, `npm test`).

## Defects
None.

Non-blocking observations, for possible follow-up backlog tasks:
- `npm pack` packs only the root package. Workspace monorepos such as support.js pack with `--workspaces --include-workspace-root`, which this adapter does not offer. The spec does not require it.
- `write_version` (pre-existing, outside this diff) updates `package.json` only, so `package-lock.json`'s `version` drifts after a release freeze.

## Process Gaps
None. The undeclared edit to `tests/test_devops.py` (one line in the pinned `__all__`) is recorded in the Execution Log. The red phase, the full suite, and both integration checks are recorded in validation-proof.md.

## Required Rework
None.
