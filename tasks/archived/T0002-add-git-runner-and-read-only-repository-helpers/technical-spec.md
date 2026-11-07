### Declared Files
- src/support_python/git.py
- tests/test_git.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md
- pyproject.toml

Size estimate: 7 files, 400 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: run_git_command builds ['git', '--no-optional-locks', ...] and omits the flag when no_optional_locks is False (patched subprocess.run).
- Unit: run_git_command merges DEFAULT_GIT_ENV and the caller env over os.environ and passes input_data as stdin.
- Unit: run_git_command raises CalledProcessError for return codes outside allowed_returncodes and returns normally for allowed ones.
- Unit: run_git_command propagates TimeoutExpired and OSError when git is missing.
- Unit: parse_status_porcelain and parse_worktree_porcelain parse fixture output, including renames, untracked entries, and detached HEAD.
- Unit: The query helpers return None (not raise) outside a repository, including is_git_clean and has_remote.
- Integration: In a temporary repository (git init with an explicit identity via -c, so CI runners without one pass): empty repo, first commit, branch creation, dirty and clean states, remote added, and a second worktree each report the expected values from the helpers.

Completion check: python -m pytest tests/test_git.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Read-only helpers plus run_git_command only; mutating helpers stay in plan until a second consumer needs them.
- **[Decided]** Tests set the git identity explicitly, matching the earlier CI fix for the namespace script tests.

- **[Decided]** User requested consistent None results on query failures, with explicit documentation distinguishing False.
- Unit: Boolean queries distinguish negative results from execution failures, including missing Git and timeouts.
- **[Decided]** Preserve Windows console suppression from the source runner as private implementation helpers.

- **[Decided]** Added pyproject.toml to synchronize the changelog version, bringing the declared count to eight files.
- Unit: Untracked filenames containing arrow text remain ordinary paths in newline porcelain parsing.

Size note: Source docstrings, integration coverage, and failure tests exceed 400 lines within one Git subsystem.

- Unit: NUL-delimited worktree paths preserve trailing newlines.
