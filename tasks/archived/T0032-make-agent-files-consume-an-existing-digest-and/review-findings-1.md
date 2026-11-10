---
task: T0032
round: 1
verdict: approved
reviewer: "@claude-2"
reviewed_at: 2026-11-10T01:41:43Z
reviewed_commit: "b253b15"
base_commit: "836b38a"
branch: task/T0032-make-agent-files-consume-an-existing-digest-and
---
# Review Findings: Task T0032 (Round 1)

## Summary
The work meets every goal; approved.
- `get_digest_generator` and `ensure_digest` are gone; `sync` and `check` only call `load_digest()`.
- Defaults are `agent-digest.md` and `agent-skills`, resolved under the project root or config directory.
- A missing or empty digest exits 1 with an `agent-digest generate <PATH>... --digest ... --skills-dir ...` hint.
  This covers `sync`, `check`, and `sync --dry-run`.
- Explicit `--digest`, `--skills-dir`, and config keys still override the defaults (unit-tested).
- Docs, README, and CHANGELOG are updated; CHANGELOG marks the change `**[breaking]**`.

Reviewer verification on `b253b15`:
- `.venv/Scripts/python -m pytest -q`: 749 passed, 3 skipped, 81 subtests passed.
- `ruff check .` and `ruff format --check .`: clean.
- `lint-markdown check docs/tools/agent-files.md`: succeeded.
- Installed `agent-files.exe` and `agent-digest.exe` exist in `.venv`.
  So `test_installed_agent_files_sync_and_check_integration` exercised the real console scripts.
- Manual `agent-files sync --dry-run` in an empty temp repo exited 1 with the expected hint.
- `NoDigestGenerationTests` runs check/sync/check in a subprocess.
  It asserts exit codes `[1, 0, 0]` and that `support_python.tools.agent_digest` never loads.

## Defects
None blocking. Minor observations only:
- The `--digest` and `--skills-dir` help says `default: ./agent-digest.md`.
  The real default resolves under the project root, not the working directory.
  The docs say `{{repo-root}}/...` correctly, and the help matches the task's goal wording.
- `MARKER_BEGIN` still says "edit guidelines/agent-digest.md in the dev-guidelines repo".
  This is a recorded **[Decided]** choice that keeps installed guarded blocks matching.

## Process Gaps
None blocking:
- The Read, red-phase, and Doc log entries come after the first Implement/Verify entries.
  They were added after completion validation flagged TF020.
  The red-phase output in validation-proof.md lists 13 specific failures and looks genuine.
  Tests and implementation landed in one commit, so git history cannot confirm test-first order on its own.
- Sibling dev-guidelines has no `.agent-files.json`, and its digest lives at `guidelines/agent-digest.md`.
  After this change, `agent-files` run there with no config exits 1.
  Its existing task T0187 already plans an agent-files config.
  But T0187 still says `agent-files.json` and `support-python agent-files check`.
  It should name `.agent-files.json` with `digest_path`/`skills_dir`, or a `agent-digest generate` step.

## Required Rework
None.
