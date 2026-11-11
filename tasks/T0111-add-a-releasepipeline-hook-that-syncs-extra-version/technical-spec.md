## Technical Specification

### Problem
`ReleasePipeline._plan` starts the next `-pre` version by editing only `CHANGELOG.md` and the project version file, then commits and pushes ("Started version X after the Y release."). Projects that keep component versions elsewhere (todos.server keeps a server and four client versions in lockstep, checked by its `check`) are left in drift, so CI on that commit fails. todos.server worked around it by overriding `Project.release` (todos.server T0238); that override can go once this ships.

### Proposal
Add an optional hook to `ReleasePipeline` and `Project`, for example `sync_versions: Callable[[str], list[str]]`. It receives the next version and returns the repo-relative paths it changed. `_plan` runs it after `_set_version(next_version)` and adds the returned paths to the `git add` of the "Started version" commit, so no second commit is needed. Dry runs list it as a planned step. Version files stay out of the release commit, which freezes the already-synced state.

Expose it through `Project` (a `sync_versions(version)` method, default no-op) so `DevopsCli._release` passes it to the pipeline.

### Tests
- Unit: the hook runs after the next-version edit and before `git add`; its paths are staged; dry run lists the step and changes nothing; a failing hook aborts before the commit and push; the default (no hook) plans the same steps as today.
- Integration: a `DevopsCli` release in a temp git repo with a hook that edits a second file leaves that file in the "Started version" commit.

### Declared Files
- src/support_python/devops/release.py
- src/support_python/devops/projects.py
- src/support_python/devops/cli.py
- tests/test_devops_release_pipeline.py
- docs/devops.md
- CHANGELOG.md

Completion check: Run the release pipeline tests, including the CLI integration scenario, and Ruff checks.

Size estimate: 6 files, 200 lines
