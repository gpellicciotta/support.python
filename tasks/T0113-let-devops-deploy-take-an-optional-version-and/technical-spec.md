### Behavior
- `deploy [VERSION]` takes an optional version, with or without a leading `v`. Bare `deploy` keeps today's behavior.
- With a version, `deploy` runs these checks in order, before creating anything:
  - The tag `v{{version}}` exists on origin; its commit is the deploy source.
  - The source has no `-pre` suffix.
- It then creates a detached `git worktree` of the tag in a temporary folder outside the repository.
- It reads the version from the worktree and checks that it matches the argument.
- The CI check uses the tag commit instead of HEAD.
- The dirty-tree and "tag points at HEAD" checks apply to bare `deploy` only.
- The typed confirmation names the tag and the temporary folder.
- Removal of the worktree runs in a `finally`, on success, failure, and rollback.
  - A removal failure, such as a Windows file lock, retries then logs a warning with the folder path. It never changes the exit code.
- `--dry-run` verifies the tag on origin and prints the plan with the folder it would use. It creates no worktree.
- The user's working tree, index, and current branch are never touched.

### Design
- Command steps run through `project.runner(argv, project.root, logger)`, and action steps and `verify` read `context.project.root`. Neither can target another folder yet.
- Add `root` to `DeployContext`, defaulting to `project.root`, and run command steps there.
- Document that action steps and `verify` must use `context.root`, not `context.project.root`.
- Pass `--recurse-submodules` when the repository has submodules.
- Untracked and ignored files are not in the worktree. Out of scope: no project needs them today.

### Declared Files
- src/support_python/devops/deploy.py
- src/support_python/devops/cli.py
- tests/test_devops_deploy.py
- docs/tutorials/devops-scripts.md

### Tests
- Unit: dirty source tree ignored with a version; missing tag on origin fails before any worktree exists.
- Unit: steps run with the worktree as root; `context.root` equals it.
- Unit: worktree removed after success, step failure, and verify failure; removal failure only warns.
- Unit: `--dry-run` with a version creates no worktree; bare `deploy` behaves as before.
- Integration: real temp git repo with a bare origin and tag; deploy from a later commit; original checkout stays untouched.

Size estimate: 4 files, 260 lines
Completion check: `python -m pytest tests/test_devops_deploy.py` and the integration scenario above pass.
