---
task: T0012
round: 1
verdict: rejected
reviewer: "@claude"
reviewed_at: 2026-11-07T14:02:48Z
reviewed_commit: "b674686"
base_commit: "fbc3e07"
branch: task/T0012-make-cloudsqlproxymanager-find-cloud-sql-proxy-outside-path
---
# Review Findings: Task T0012 (Round 1)

## Summary
The core goal is met. `resolve_cloud_sql_proxy_bin` now searches fallback directories (`~/bin`, `~/.local/bin`, Cloud SDK, gcloud sibling, and others). `CloudSqlProxyManager.start` returns 1 with a clear error when neither the binary nor Docker exists, and when `subprocess.run` raises `OSError`.

Verification, run in the task worktree (pytest sets `pythonpath = ["src"]`, so the worktree code was tested):
- Full suite: `503 passed, 3 skipped`.
- `tests/test_devops.py`: 47 passed.
- `ruff check .`: clean.
- `ruff format --check .`: clean.

Rejected for one correctness defect (D1) plus scope and documentation gaps that should be fixed in the same pass.

## Defects
- **D1 (medium, correctness): legacy v1 binary names are resolved but launched with v2-only arguments.**
  - `_PROXY_PATH_NAMES` and `_PROXY_FILE_NAMES` in `src/support_python/devops.py` now include `cloud_sql_proxy` and `cloud_sql_proxy.exe`. That is the deprecated v1 proxy, and `gcloud components install` historically places it in the Cloud SDK `bin` directory.
  - `start()` always builds v2 syntax: positional instance, `--address`, `--port`, `--credentials-file`.
  - v1 uses `-instances=...`, `-credential_file`, and similar flags, so it would fail at launch with a confusing error.
  - `test_finds_proxy_next_to_gcloud_outside_path` locks this in by asserting that `cloud_sql_proxy.exe` is accepted.
  - The task asked to find `cloud-sql-proxy`, not v1.
  - Before this change, a machine with only v1 fell back to Docker. It now picks the incompatible v1 binary instead.
- **D2 (minor): unrequested and undocumented `CLOUD_SQL_PROXY_BIN` environment override.**
  - It is the first lookup and takes precedence over everything else.
  - It appears in no README, `docs/`, or CHANGELOG entry, and no ADR or task spec covers it.
  - Either document it (README, `docs/devops.md`, CHANGELOG) or remove it.
- **D3 (minor): stale log message.**
  - `start()` still logs "Local cloud-sql-proxy binary not found on PATH; falling back to Docker image...".
  - That is now misleading, because the search covers `repo_root` and the fallback directories.
- **D4 (minor): version bump without need.**
  - The top CHANGELOG heading and `pyproject.toml` went from `v1.0.11-pre` to `v1.0.12-pre`.
  - `v1.0.11-pre` was still an unfrozen `-pre` section, so the other unreleased entries (T0001, T0003, T0007) were silently renamed into 1.0.12.
  - Under the project convention, new entries belong in the existing `-pre` section.

## Process Gaps
- The task file has no `## Technical Specifications` or `### Tests` section.
  - The global rules require unit and integration test specs for code-modifying tasks. Only the scaffold remains.
  - The Task Execution Steps (Implement, Verify, Doc, Review) have no dedicated TDD steps.
  - The log asserts tests were written first and failed, with no recorded failing output.
- The log says "live smoke check" but records no command or output.
- `docs/requirements.md`, `docs/devops.md`, and the CLAUDE.md architecture text do not mention the new discovery behavior. Only a README comment line was updated.

## Required Rework
1. Fix D1. Either:
   - drop the `cloud_sql_proxy*` names from both name tuples and fix the gcloud-sibling test to use `cloud-sql-proxy`, or
   - detect v1 and build v1-compatible arguments (a larger change; not recommended).
2. Resolve D2: document `CLOUD_SQL_PROXY_BIN` in the README, `docs/devops.md`, and CHANGELOG, or remove it with its test.
3. Update the Docker-fallback log message (D3) to say the binary was not found on `PATH` or in the fallback locations.
4. Resolve D4: keep the version at `1.0.11-pre` and CHANGELOG under the existing heading, or justify the bump in the task file.
5. Add `## Technical Specifications` / `### Tests` to the task file listing the unit and integration cases, and record the failing-first evidence and the smoke-check command with its output in the Execution Log.
6. Re-run the full pytest suite and `ruff check` / `ruff format --check`, and record the results.
