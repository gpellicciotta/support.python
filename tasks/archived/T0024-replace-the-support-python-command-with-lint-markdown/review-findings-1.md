---
task: T0024
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T20:00:18Z
reviewed_commit: "decca33"
base_commit: "decca33"
branch: task/T0024-replace-the-support-python-command-with-lint-markdown
---
# Review Findings: Task T0024 (Round 1)

## Summary
Reviewed branch tip `2957fd7` (base `886c224`), not `decca33`.
The worktree sits in an unfinished rebase onto `decca33`, so `main..HEAD` is empty there.
I exported `2957fd7` into a clean temporary venv and verified it there:
- `pip install -e ".[dev]"` installs exactly `processes`, `agent-files`, `lint-markdown`, and `git-repository-backup`.
- Each tool's `version` action exits 0 and prints its banner.
- `lint-markdown check --offline docs` exits 0.
- `import support_python.__main__` raises `ModuleNotFoundError`.
- `ruff check .` and `ruff format --check .` pass.
- `python -m pytest -q` gives 693 passed, 3 skipped.

The core change matches the spec: the pyproject scripts table, the `cli.py` removals, the `TOOL_NAME` rename, the file deletions, and the README install section.
I rejected it because live docs and a user-facing message still name commands that no longer exist.
The new console-script tests also break in standard POSIX venvs.

## Defects
1. **Stale docs still advertise the removed `support-python` command.**
   - `docs/index.md:19-20`, a mandatory doc, says the linter and agent-files sync are "exposed via `support-python lint markdown`" and "`support-python agent-files`".
   - `CLAUDE.md:28-29` still tells agents to "Run the demo CLI: `support-python greet <name>`" or `python -m support_python.cli greet`. Both are gone.
   - `CLAUDE.md:37` and `CLAUDE.md:44` still say "exposed via `support-python agent-files`" and "`support-python lint markdown`".
   - The project conventions treat doc drift as a bug. The task goal is to remove the command, so these references are in scope.
2. **A user-facing message names a command that does not exist.**
   - `src/support_python/agent_files.py:275` tells users to "run 'generate-agent-digest' or 'update-global-agent-files update'".
   - The tool is now `agent-files`, so the hint should read `agent-files update`.
   - The spec required grepping `src` for leftover uses of removed names.
3. **Console-script lookup fails in POSIX venvs.**
   - `tests/test_console_scripts.py:26` and `tests/test_processes_cli.py:151` find scripts via `Path(sys.executable).resolve().parent`.
   - On Linux/macOS, `.venv/bin/python` is a symlink to the base interpreter. `resolve()` follows it to e.g. `/usr/bin`, where the console scripts are not installed.
   - A developer using `scripts/bootstrap-dev-environment.py` on POSIX would see these tests fail with "Console script ... not found".
   - CI passes only because `ubuntu-latest` installs into the toolcache interpreter without a venv. Windows passes because the venv launcher is not a symlink.
4. **Minor:** `tests/test_console_scripts.py:122` asserts `"markdown files" in stdout or "docs" in stdout`. The startup banner prints the working directory, so the `"docs"` branch is close to vacuous. Assert the summary line instead.
5. **Minor:** the module docstring at `tests/test_agent_files.py:3` still describes `scripts/update-global-agent-files.py`.

## Process Gaps
1. **The branch does not merge cleanly with `main`, and the worktree was left broken.**
   - `main` moved to `v2.0.2-pre` with T0034. The branch's CHANGELOG entry sits under `v2.0.1-pre`, so it conflicts.
   - The worktree is left mid-`git rebase` with `CHANGELOG.md` unmerged (`UU`), and HEAD is detached at `decca33`.
   - The validation evidence (`2.0.1-pre+886c224`) was collected before T0034, not on the rebased state.
2. The Execution Log has no Verify entry recording the red-phase run. The red-phase proof exists only in `validation-proof.md`. This is acceptable but thin.
3. The size estimate (11 files, 350 lines) left out the four undeclared test files and the deletions. The work loop flagged and approved this, so no rework is needed.

## Required Rework
1. Replace the stale `support-python` references in `docs/index.md:19-20` and `CLAUDE.md:28-29,37,44` with `lint-markdown`, `agent-files`, and the other console scripts. Drop the demo-CLI command line.
2. Change the hint at `src/support_python/agent_files.py:275` to `agent-files update`, and fix the `tests/test_agent_files.py:3` docstring.
3. Resolve console scripts portably, for example with `sysconfig.get_path("scripts")` or `Path(sys.executable).parent` without `resolve()`. Apply the fix in both `tests/test_console_scripts.py` and `tests/test_processes_cli.py`.
4. Finish or restart the rebase onto current `main`. Move the CHANGELOG entry under `## v2.0.2-pre` and keep `pyproject.toml` at `2.0.2-pre`.
5. Re-run `pip install -e ".[dev]"`, `pytest -q`, `ruff check .`, and each console script's `version` action on the rebased branch. Record the output in `validation-proof.md`.
