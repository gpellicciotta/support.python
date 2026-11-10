# Adapter-Specific DevopsCli Help

## Technical Specifications
### Design Decisions
- **[Decided]** `Project.action_summaries()` returns a summary override per action; the base returns none.
- **[Decided]** `test_selection_example` is a class attribute; an empty value drops the `test` example.
- **[Decided]** Python and Node keep the generic summaries; only `GradleProject` overrides them.

### Tests
- Unit: Gradle help names each action's tasks and follows task-list overrides.
- Unit: Gradle help names `release_task`, and its verbose examples use `com.example.AppTest`.
- Unit: `release --dry-run --skip-checks` with a `release_task` warns and runs only the Gradle dry run.
- Unit: Python help keeps the pytest example and generic summaries; Node help uses `test/cli.test.js`.
- Integration: template.java's `devops.py` on a `GradleProject` prints the new summaries (checked by hand here).

Completion check: `python scripts/devops.py check`

### Declared Files
- `src/support_python/devops/cli.py`
- `src/support_python/devops/projects.py`
- `tests/test_devops_cli.py`
- `tests/test_devops_projects_gradle.py`
- `tests/test_devops_projects_node.py`
- `docs/tutorials/devops-scripts.md`
- `CHANGELOG.md`
