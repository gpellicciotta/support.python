---
task: T0042
round: 1
verdict: rejected
reviewer: "@claude-2"
reviewed_at: 2026-11-10T04:06:59Z
reviewed_commit: "bae339a"
base_commit: "026879e"
branch: task/T0042-add-opt-in-docker-db-server-mail-and
---
# Review Findings: Task T0042 (Round 1)

## Summary
The dispatch design is clean and well tested against mocks.
Registration, sub-action dispatch, exit 2 on unknown sub-actions, and help output all work.
Reviewer evidence on `bae339a`:
- `pytest -q`: 1023 passed, 3 skipped, 114 subtests passed.
- `ruff check .` and `ruff format --check .`: clean.
- `pytest -q tests/test_devops_service_actions.py tests/test_devops.py`: 96 passed.

One goal is not met: "covering the counters.server and todos.server variants" so consumers can replace their copies.
The CLI accepts any `db_targets` value, but `LocalMySqlManager.load_snapshot` rejects `todos_test`.
The README example advertises exactly that broken configuration.
Mocked tests hide the gap.

## Defects
1. **`todos_test` target documented and accepted, but fails at runtime.**
   - README example: `db_targets=("local", "testdb", "todos_test")`.
   - `LocalMySqlManager.load_snapshot` (`src/support_python/devops/services.py`, around line 719) accepts only `testdb`, `auth_test`, and `counters_test`.
   - Reproduced with a real `LocalMySqlManager` and an existing snapshot file:
     ```text
     devops db load-snapshot s.sql --target todos_test
     **[ERROR]** Invalid target 'todos_test'. Allowed targets are 'local' and 'testdb'.
     exit 1
     ```
   - `db snapshot --load-target todos_test` reaches the same branch.
   - `test_load_target_choices_come_from_db_targets` passes `todos_test` to an autospec mock, so the suite cannot catch this.
   - Effect: todos.server cannot replace its copy, contrary to the goal and the spec ("covering the counters.server and todos.server variants").
2. **Minor (non-blocking): the shared `db` parser silently swallows a stray positional.**
   - `devops db snapshot stray.sql` binds `stray.sql` to `snapshot_path` and ignores it, without warning.
   - Only `load-snapshot` reads it.
   - Consider rejecting `snapshot_path` for other sub-actions with exit 2.

## Process Gaps
1. **Undisclosed option omissions.**
   - The spec says to copy option names from `../auth/scripts/devops.py` lines 1841-1923.
   - Two options in that range are missing: `server start --testdb` (auth line 1880) and `client verify-deployment --timeout` (auth line 1892).
   - counters.server and todos.server also expose `--testdb`.
   - The 2026-11-10 `[Decide]` entry lists the deviations but leaves these two out.
   - The managers may not support them (`LocalServerManager.start` has no testdb parameter, and `verify_deployment` has no timeout), but the omission should be recorded as a decision.
2. Integration coverage for `db` targets uses mocks only, so no test exercises the real `load_snapshot` target check.
   - Fixing defect 1 should include a test against the real manager's target dispatch. That test needs no Docker, because the invalid-target branch runs before any subprocess call.

## Required Rework
1. Make every target the CLI accepts work end to end, choosing one approach:
   - Extend `LocalMySqlManager.load_snapshot` to accept configured test-database aliases, such as `{db_name}_test` or an explicit alias set passed from `db_targets`. Keep the error message accurate.
   - Or validate `db_targets` against the targets the manager supports, and fix the README example and CHANGELOG wording.
2. Add a test that runs `db load-snapshot --target <alias>` through a real (not mocked) `LocalMySqlManager`, patching only the subprocess or port probe. It must fail before the fix and pass after.
3. Record in the Execution Log a `[Decide]` entry on `server start --testdb` and `client verify-deployment --timeout`: either implement them or state why they are out of scope.
