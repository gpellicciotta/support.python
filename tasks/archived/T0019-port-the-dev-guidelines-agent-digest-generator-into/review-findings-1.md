---
task: T0019
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-09T23:52:07Z
reviewed_commit: "606bfa4"
base_commit: "203bf3a"
branch: task/T0019-port-the-dev-guidelines-agent-digest-generator-into
---
# Review Findings: Task T0019 (Round 1)

## Summary
Rejected. The port itself is faithful, but the agent-files wiring regresses `--repo-root` behavior.

Verified by the reviewer:
- `diff` against dev-guidelines `38e0de0` shows only import, harness, tool-name, and repo-root resolution changes.
- Ported tests match the original 40 cases (plus 2 new ones); real-repo tests moved onto `tests/fixtures/agent_digest/`.
- Full suite: `753 passed, 3 skipped, 85 subtests passed`, exit 0.
- `ruff check .` and `ruff format --check .` are clean.
- Integration: in a `git archive 38e0de0` copy, `agent-digest check|validate|generate` exit 0, and `diff -r` against a pristine copy shows no changes.
- Console script, README, and CHANGELOG (v2.0.13-pre) entries are present and consistent.

## Defects
1. **[Major] `agent-files` ignores its resolved repo root when checking or regenerating the digest.**
   - `get_digest_generator` now always returns `support_python.tools.agent_digest`.
   - That module resolves its root from `Path.cwd()`, not from `agent_files.REPO_ROOT` (`--repo-root` or `.agent-files.json`).
   - Before, the script loaded from `{{repo-root}}/scripts/` and used its own location as the root.
   - Reproduction: stale `guidelines/agent-digest.md` in a `38e0de0` copy, then from an unrelated repo run `agent-files check --repo-root {{copy}} --verbose`.
     - main (`203bf3a`): emits `agent-digest.md is out of date compared to source guidelines`.
     - branch (`606bfa4`): no warning; `build_digest` raises `FileNotFoundError` against the cwd repo, which `ensure_digest` swallows at DEBUG.
   - `sync --repo-root` likewise no longer regenerates the digest or derived skills.
   - If cwd is inside a different guidelines checkout, `sync` writes that checkout's digest and skills into the `--repo-root` target.
2. **[Minor] Stale tool name in `agent_files.py`.**
   - Line 273 tells users to run `'generate-agent-digest'`; the command is now `agent-digest`.
   - The `ensure_digest` docstring (line 238) still refers to `generate-agent-digest`.
3. **[Minor] Dead code.**
   - `_INITIAL_DIGEST_PATH` in `agent_digest.py` is never read.
   - `_MODULE_PATH` in `tests/tools/test_agent_digest.py` is never read.

## Process Gaps
- The new `test_agent_files_get_digest_generator_returns_packaged_module_without_script` only asserts module identity. No test covers `ensure_digest` with `--repo-root` (or a config `repo_root`) differing from cwd, so defect 1 went undetected.
- `validation-proof.md` runs the integration check only from inside the dev-guidelines copy. It never runs the `agent-files` digest path, the only runtime caller of `get_digest_generator`.

## Required Rework
1. Make `ensure_digest` build the digest and skills against `agent_files._resolve_repo_root()`.
   - Do not just pass `source_dir=` explicitly. With a non-default `source_dir`, `build_digest` silently skips missing source files.
   - In a repo whose `guidelines/` lacks the sources, `sync` would then overwrite its `agent-digest.md` with a near-empty digest.
   - Safer options: temporarily point `agent_digest.REPO_ROOT` at the resolved root, or add an explicit root parameter. Keep the missing-source `FileNotFoundError` fallback.
2. Add a failing-first test: fixture copy with a stale digest, cwd in an unrelated repo.
   - `agent-files check --repo-root {{copy}}` warns that the digest is out of date.
   - `agent-files sync --repo-root {{copy}}` regenerates it.
   - Neither touches the cwd repo.
3. Replace `generate-agent-digest` with `agent-digest` in `agent_files.py` lines 238 and 273.
4. Remove `_INITIAL_DIGEST_PATH` and the unused test `_MODULE_PATH`.
5. Record the new test run and the `--repo-root` reproduction in `validation-proof.md`.
