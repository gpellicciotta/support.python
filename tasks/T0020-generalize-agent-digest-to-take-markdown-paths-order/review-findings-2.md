---
task: T0020
round: 2
verdict: approved
reviewer: "@claude"
reviewed_at: 2026-11-10T00:41:38Z
reviewed_commit: "af98d9f"
base_commit: "2e7ca39"
branch: task/T0020-generalize-agent-digest-to-take-markdown-paths-order
---
# Review Findings: Task T0020 (Round 2)

## Summary
Round 2 resolves every round-1 defect and process gap; the work meets the task goals.
Verified by the reviewer against the worktree source at `af98d9f`:
- `python -m pytest tests -q` (`PYTHONPATH=src`): 738 passed, 3 skipped, 81 subtests passed.
- `ruff check .` and `ruff format --check .`: clean.
- `lint-markdown check docs/tools/agent-digest.md --offline`: clean.
  Issues reported in README.md and CHANGELOG.md sit on lines this branch did not touch.
- Red phase: the delivered `test_agent_digest.py` against the `2e7ca39` module (`-o pythonpath=<base>/src`) gave 26 failed, 11 passed, 4 subtests passed.
  This matches `validation-proof.md` exactly.
- Integration on a fresh clone of dev-guidelines (`369a963`, `origin` set to its GitHub URL):
  - `generate guidelines --digest guidelines/agent-digest.md --skills-dir skills` exited 0 and left `git status --short` empty.
  - `check guidelines ... --skill-index guidelines/general-guidelines.md` exited 0.
- Without `origin`, `generate` exits 0 and keeps repository links relative.
  The new `or ""` fallback derives the link base once per build, not once per file.

`docs/tools/agent-digest.md` now matches the code: the options, front-matter keys, link rewriting, `check` rules, and exit codes.
The startup banner prints `Digest` and `Skills dir` with forward slashes.

## Defects
None.

Non-blocking observations carried from round 1 (no rework required):
- `--skill-index` is still a global option, so `generate` accepts it and silently ignores it.
- `DigestHarness.run` still duplicates the path validation that the actions perform.
- Each action still calls `collect_input_files` several times, re-reading every input file.
- Front-matter and non-integer `index` errors name `filepath.name`, which is ambiguous when inputs share a basename.
  The docs now say "names the offending file", which is accurate.
- `agent-files` derives the link base from the current branch.
  CI builds on non-main or detached checkouts of dev-guidelines need an explicit `--link-base`.

## Process Gaps
None blocking.
- The `check` integration log in `validation-proof.md` shows version `v2.0.14-pre+2e7ca39`, while `generate` shows `+5be8119`.
  The banner layout proves the new code ran, so the suffix most likely comes from stale installed build metadata.
  The reviewer's own run confirms that `check` passes.

## Required Rework
None.
