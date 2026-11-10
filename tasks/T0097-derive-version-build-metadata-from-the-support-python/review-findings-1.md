---
task: T0097
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-10T21:10:08Z
reviewed_commit: "680b4e7"
base_commit: "4b44ff9"
branch: task/T0097-derive-version-build-metadata-from-the-support-python
---
# Review Findings: Task T0097 (Round 1)

## Summary
The stated goal is met. A wheel installed into a venv inside a foreign Git repository no longer shows the foreign hash.
Install-time `direct_url.json` commits are read, and editable or source checkouts still report their own hash.
The change introduces a regression for consumer tools that sit at the root of a repository holding their own `.venv`.

Evidence:
- `pytest tests/test_cli.py` passed: 35 passed, 25 subtests passed. The new wheel-in-foreign-venv integration test passed.
- `ruff check` and `ruff format --check` were clean.
- The full suite had 1227 passed, 3 skipped, and 1 error. The error was the conftest user-state guard, which fired on `~/.claude/skills/synced` files outside this change.

## Defects
1. `_is_support_python_target` in `src/support_python/cli.py` treats `work_dir in package_dir.parents` as "this is support-python".
   - A consumer tool whose `repo_dir` is the root of its own repository, with support-python installed in `<root>/.venv/.../site-packages/support_python`, now matches.
   - That path returns the install commit or `unknown`, never the consumer's own hash.
   - Reproduced in a temp repo (hash `b071dea`): `resolve_build_metadata(<repo root>)` returned `'unknown'` with the package under `.venv/Lib/site-packages`.
   - Before this change, it returned the consumer repository's own hash. `ToolHarness` passes `cwd=self.repo_dir`, so such tools lose their build metadata.
   - The `work_dir.name == "support_python"` and `tools`/`devops`/`markdown` name heuristics are also fragile. Compare resolved paths instead.

## Process Gaps
- No test covers the positive source/editable-checkout path of the new logic: support-python checkout gives its hash.
- No test covers a foreign tool's own hash being kept (the regression above).

## Required Rework
1. Narrow the "support-python target" test to `work_dir` being the package directory or inside it (or inside the support-python checkout root).
   - Do not match when `work_dir` is merely an ancestor of the package.
   - Do not match by directory name.
2. Add a unit test: a foreign repo with a `.venv/.../site-packages/support_python` package, with `cwd` at the repo root, keeps its own hash.
3. Add a unit test for the editable or source checkout path returning the checkout hash.
