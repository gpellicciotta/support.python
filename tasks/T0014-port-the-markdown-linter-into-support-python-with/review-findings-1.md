---
task: T0014
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T16:54:01Z
reviewed_commit: "ec21004"
base_commit: "37cd186"
branch: task/T0014-port-the-markdown-linter-into-support-python-with
---
# Review Findings: Task T0014 (Round 1)

## Summary
The port is close to the original and mostly meets the goals, but it has one behavioral regression that the ported tests hide.

Verified:
- The `markdown_lint.py` diff against dev-guidelines `scripts/lint-markdown.py` shows only the import changes and the stream-reconfigure move.
- `tests/test_markdown_lint.py`: 115 passed.
- Full suite: 652 passed, 3 skipped, 1 failed. The failure is `test_processes.py::test_child_process_lifecycle_integration`. It passes when `tests/test_processes.py` runs alone (27 passed), so it looks flaky and unrelated to T0014.
- `ruff check .` and `ruff format --check .` pass.
- `support-python lint markdown --offline` on dev-guidelines gives the same output as the original script. The only differences are the version string and timing.

## Defects
1. **`REPO_ROOT` points at `src/` instead of the repository root** (`src/support_python/markdown_lint.py:30`).
   - The original `Path(__file__).resolve().parent.parent` was the repo root, because the script lived in `scripts/`. After the move it resolves to `<checkout>/src`.
   - Line 474 resolves `github.com/gpellicciotta/dev-guidelines/blob/...` URLs against `REPO_ROOT`. Sibling repositories resolve against `REPO_ROOT.parent`, which is now the repo root and not the workspace.
   - Line 993 resolves root-relative links such as `/docs/x.md` against `REPO_ROOT`.
   - Both lookups now use the wrong base, which gives false results.
   - When the package is installed, the root is `site-packages`.
   - The ported tests hide the bug. `test_markdown_lint.py` patches `REPO_ROOT` to `SRC_DIR.parent`, and it rewrote the fixtures to use `src/support_python/cli.py`. The suite therefore passes while the real default is wrong.
   - The task required "identical rules and output". The on-disk checks agree only because dev-guidelines has no such links.

## Process Gaps
- The task says "unchanged apart from imports", but `REPO_ROOT` needed a change because the file moved. The Execution Log notes reading "REPO_ROOT usage" but records no decision about it.
- Several tests were edited rather than ported verbatim, and their test fixtures hide the bug. The Execution Log does not record these edits or the reason for them.
- `README.md` has no `lint markdown` usage section. `CLAUDE.md` treats README drift as a bug.
- The Execution Log claims "identical output against dev-guidelines" without noting the version-string difference or the Python `-m` RuntimeWarning. Both are harmless.
- The task file says `tests/` and `docs/` changes were needed, but it records no decision for the version bump to `1.0.19-pre`. This is minor.

## Required Rework
1. Make `REPO_ROOT` resolve to the checked-out repository root regardless of module location.
   - For example, derive it from the current working directory, or from the nearest ancestor directory that contains `.git`.
   - Alternatively, accept an explicit root.
   - Record the decision with `**[Decided]**` in the Execution Log.
2. Restore the original link-resolution tests unchanged (the `generate-agent-digest.py` and `scripts/` fixtures). Run them from a temporary repository fixture, or patch the root explicitly.
   - They must fail without the `REPO_ROOT` fix and pass with it.
3. Add a README (or docs) usage entry for `support-python lint markdown`.
4. Re-run the full suite and ruff. If `test_child_process_lifecycle_integration` fails again, note that it is unrelated.
