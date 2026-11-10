---
id: T0037
owner: "@claude"
session: claude-20261110-2e468e
needs: []
branch: task/T0037-rebuild-extract-release-notes-migrate-namespace-and-reset
worktree: .plan/work/T0037-rebuild-extract-release-notes-migrate-namespace-and-reset
status: active
started_at: "2026-11-10T02:30:54Z"
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0037: Rebuild extract-release-notes, migrate-namespace, and reset-history on support_python.devops.release, and delete scripts/_repo_common.py

## Goals
Rebuild `scripts/extract-release-notes.py`, `scripts/migrate-namespace.py`, and `scripts/reset-history.py` on `support_python.devops.release`, and delete `scripts/_repo_common.py`.
Make them act on the Git repository containing the current directory, not on this script's repository.
Keep their actions, options, prompts, and outputs otherwise unchanged.
Leave `scripts/install-from-github-release.py` self-contained and untouched.

## Task Execution Steps
- [x] **[Read]**      Read the three scripts, scripts/_repo_common.py, their tests, and support_python.git.
- [x] **[Implement]** Write failing tests for running each script from another repository's directory.
- [x] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [x] **[Implement]** Rebuild the scripts on the library, add missing Git queries, and delete _repo_common.py.
- [x] **[Verify]**    Run the full suite and the integration commands from the technical spec.
- [x] **[Doc]**       Update README.md and CHANGELOG.md for the scripts' new repository targeting.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided on 2026-11-09 that these scripts stay uninstalled; acting on the current directory's repository removes any need to copy them.

- [2026-11-10] **[Verify]**
  Red phase: new tests fail before implementation.
  - test_git.py: AttributeError, get_default_branch missing.
  - 6 script tests failed: wrong repository, no outside-repo error.
  - Mutating tests deselected; old scripts would target this worktree.

- [2026-11-10] **[Implement]**
  Rebuilt the three scripts on support_python, added Git remote and default-branch queries, and deleted _repo_common.py.
  - Undeclared: __init__.py re-exports, release.py regex dedupe.
  - Undeclared: README.md and docs/devops.md references.

- [2026-11-10] **[Decided]**
  Explicit changelog paths skip repository resolution; finish uses extract_release_notes, fixing empty release notes.

- [2026-11-10] **[Verify]**
  Recorded size note after crossing the typical line.
  - Size note: 12 files, ~493 lines; small export and doc fix-ups.
  - Splitting would leave docs referencing the deleted helper.

- [2026-11-10] **[Verify]**
  Full suite, ruff, and spec integration commands pass; 1.3.5 output matches baseline.
  - 860 passed, 3 skipped.
  - Proof in validation-proof.md.

- [2026-11-10] **[Doc]**
  Documented repository targeting in README.md, docs/devops.md, and CHANGELOG.md.

