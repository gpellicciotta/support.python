# Git Helpers

[git.py](../../src/support_python/git.py) provides a Git command runner and read-only repository queries.
Its symbols are re-exported from `support_python` and also available through `support_python.git`.
Git must be installed and available on `PATH`; no Python dependencies are required.

## Repository queries

```python
from support_python import get_repo_root, has_remote, is_git_clean

root = get_repo_root(".")
clean = is_git_clean(".")
if clean is None:
    print("Repository status could not be queried")
elif clean:
    print("Working tree is clean")
else:
    print("Working tree has changes")

remote = has_remote(".", "origin")  # True: configured; False: absent; None: query failed.
```

All repository queries return `None` on execution failure, including missing Git, timeouts, and invalid repositories.
`is_git_clean`, `has_remote`, and `branch_exists` return `False` only for confirmed negative results.
Use `result is None` to distinguish failures from negative results.
This intentionally differs from plan's original clean and remote helpers, which returned `False` on errors.
`get_head_commit` also returns `None` before the first commit.
`get_current_branch` returns `"(detached)"` for detached HEAD.
An unborn branch has a symbolic name but does not yet exist as a branch ref.

## Status and worktree parsing
`get_working_tree_status` returns dictionaries containing `status`, `path`, and optional `original_path` for renames or copies.
`list_worktrees` returns dictionaries using Git's porcelain keys, including `worktree`, `HEAD`, `branch`, and optional flags.
Flags such as `detached` have empty string values.
Both queries use NUL-delimited output to preserve filenames containing whitespace, quotes, or newlines.
`parse_status_porcelain` and `parse_worktree_porcelain` also accept newline-delimited output for simple fixtures.
Newline status parsing does not decode Git's quoted escape sequences; use NUL-delimited output for arbitrary filenames.

## Command runner
`run_git_command(cwd, *args)` returns `subprocess.CompletedProcess[str]` with UTF-8 stdout and stderr.
It raises `CalledProcessError` for disallowed exit codes, `TimeoutExpired` for timeouts, and `OSError` for execution failures.
The default timeout is 10 seconds; `allowed_returncodes`, `env`, and `input_data` customize execution.
Defaults disable optional locks, lazy fetching, and terminal prompts; caller environment overrides take precedence.
`no_optional_locks=False` omits the command flag; override `GIT_OPTIONAL_LOCKS` separately if optional locks are needed.
The runner accepts arbitrary Git commands, including mutations; repository query helpers only inspect local state.
