---
task: T0014
round: 2
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T17:03:47Z
reviewed_commit: "9a69e81"
base_commit: "37cd186"
branch: task/T0014-port-the-markdown-linter-into-support-python-with
---
# Review Findings: Task T0014 (Round 2)

## Summary
Round 1 rework is mostly resolved, but one restored test passes only on this machine. It depends on a sibling `dev-guidelines` checkout and fails on a clean clone or in CI.

Verified:
- `REPO_ROOT` now comes from `find_project_root(Path.cwd())`. Root-relative MD014 links resolve against the file's project root, and a new fixture-based test covers it.
- GitHub sibling-repo URLs resolve against the workspace root, which is `.plan/work`-aware.
- Diff against dev-guidelines `lint-markdown.py` shows only the import changes, the `REPO_ROOT` and workspace-root changes, and the stream-reconfigure move.
- README has a `lint markdown` usage section. `docs/index.md` links to it.
- Full suite: 654 passed, 3 skipped. `tests/test_markdown_lint.py`: 116 passed. `ruff check` and `ruff format --check` are clean.
- `lint markdown --offline` on dev-guidelines gives the same output and exit code 0 as the original script. The only differences are the version banner and a harmless `-m` RuntimeWarning.

## Defects
1. **`test_local_dev_guidelines_github_url_resolves_locally` needs a sibling `dev-guidelines` checkout** (`tests/test_markdown_lint.py:613`).
   - The test links to `https://github.com/gpellicciotta/dev-guidelines/blob/main/scripts/generate-agent-digest.py`.
   - It then asserts `urlopen` is never called.
   - The project root is now `support.python`, so the target repo resolves to `<workspace>/dev-guidelines`.
   - That directory exists here, so the test passes. It does not exist in a clean clone or in `.github/workflows/python-package.yml`.
   - I reproduced this by patching `_resolve_workspace_root` to an empty directory. The result was an MD018 issue and `urlopen` called, so the test fails.
   - Round 1 required the fixtures to run from a temporary repository fixture or with an explicit root patch. This test does neither.

## Process Gaps
- The Execution Log does not record that `test_backticked_repo_file_flags_md019` and the CHANGELOG tests deviate from the originals. It also omits the `README.md` to `LICENSE.md` change and the extra CLI test.
  - The deviations are justified, since the originals depended on dev-guidelines files. They should still be logged.
- The Round 1 `**[Decided]**` entry is present. It does not mention the `_resolve_workspace_root` helper or the `repo_name == base_root.name` rule. Both change behavior from the original.

## Required Rework
1. Make `test_local_dev_guidelines_github_url_resolves_locally` self-contained.
   - Create a temporary workspace with a `dev-guidelines/scripts/generate-agent-digest.py` file, and a sibling project with a `.git` directory.
   - Lint a file in the sibling project, or patch `_resolve_workspace_root` to the temporary workspace.
   - Assert no MD018 and `urlopen` not called.
   - Optionally add a negative case for a missing file.
2. Re-run the full suite and ruff, then log the test deviations in the Execution Log.
