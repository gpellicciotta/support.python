## Walkthrough & Validation

### Red phase
Command: `.venv/Scripts/python -m pytest -q tests/test_devops_release_pipeline.py` (exit code 2)

```text
=================================== ERRORS ====================================
___________ ERROR collecting tests/test_devops_release_pipeline.py ____________
tests\test_devops_release_pipeline.py:12: in <module>
    from support_python.devops import ReleasePipeline, confirm_typed, run_step_command
E   ImportError: cannot import name 'ReleasePipeline' from 'support_python.devops'
=========================== short test summary info ===========================
ERROR tests/test_devops_release_pipeline.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.36s
```

### Green phase: new tests
Command: `.venv/Scripts/python -m pytest tests/test_devops_release_pipeline.py -v` (exit code 0)

```text
PreconditionTests::test_allows_uncommitted_version_file_and_changelog_when_freezing PASSED
PreconditionTests::test_rejects_empty_release_notes PASSED
PreconditionTests::test_rejects_existing_github_release PASSED
PreconditionTests::test_rejects_existing_local_tag PASSED
PreconditionTests::test_rejects_existing_remote_tag PASSED
PreconditionTests::test_rejects_failed_fetch PASSED
PreconditionTests::test_rejects_failed_quality_check PASSED
PreconditionTests::test_rejects_missing_asset PASSED
PreconditionTests::test_rejects_missing_gh PASSED
PreconditionTests::test_rejects_other_branch PASSED
PreconditionTests::test_rejects_unauthenticated_gh PASSED
PreconditionTests::test_rejects_uncommitted_changelog_when_already_frozen PASSED
PreconditionTests::test_rejects_unrelated_uncommitted_changes PASSED
DryRunTests::test_dry_run_changes_nothing_and_logs_every_planned_command PASSED
ConfirmationTests::test_confirm_typed_matches_the_exact_phrase PASSED
ConfirmationTests::test_confirm_typed_treats_end_of_input_as_declined PASSED
ConfirmationTests::test_declined_confirmation_changes_nothing PASSED
ConfirmationTests::test_typed_confirmation_releases PASSED
FrozenVersionTests::test_frozen_version_skips_the_freeze_commit PASSED
FullReleaseIntegrationTests::test_failed_step_exits_1 PASSED
FullReleaseIntegrationTests::test_full_release_against_a_local_bare_origin PASSED
============================= 21 passed in 29.39s =============================
```

The integration scenario uses a temporary repository with a local bare `origin`; only `gh` is stubbed.

### Full suite and linters
Commands: `.venv/Scripts/python -m pytest -q`, `ruff check .`, `ruff format --check .` (all exit code 0)

```text
834 passed, 3 skipped, 81 subtests passed in 106.85s (0:01:46)
All checks passed!
135 files already formatted
```

`lint-markdown check README.md CHANGELOG.md` reports 10 issues, all on lines this task did not touch.

### Real dry-run smoke checks
Run from the worktree with real `git` and `gh`. Both exit 1 before any change; `git status` stays clean.

```text
$ python -c "...ReleasePipeline(root=Path('.'), logger=CliLogger(), dry_run=True).run()"
Release version: v2.0.20
Next version: v2.0.21-pre
Dry run: True
**[ERROR]** Releases must be cut from branch 'main' (currently on 'task/T0036-add-a-dry-runnable-releasepipeline-that-freezes-tags').

$ python -c "...ReleasePipeline(..., main_branch='task/T0036-...', dry_run=True).run()"
**[ERROR]** Could not fetch origin/task/T0036-add-a-dry-runnable-releasepipeline-that-freezes-tags: fatal: couldn't find remote ref task/T0036-add-a-dry-runnable-releasepipeline-that-freezes-tags
```

The second run passed the real `gh --version` and `gh auth status` checks before the fetch.
