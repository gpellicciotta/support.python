---
id: T0037
owner: ~
needs: ['T0036']
branch: —
worktree: —
status: ready
started_at: —
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
- [ ] **[Read]**      Read the three scripts, scripts/_repo_common.py, their tests, and support_python.git.
- [ ] **[Implement]** Write failing tests for running each script from another repository's directory.
- [ ] **[Verify]**    Run the new tests and record their failures as red-phase proof.
- [ ] **[Implement]** Rebuild the scripts on the library, add missing Git queries, and delete _repo_common.py.
- [ ] **[Verify]**    Run the full suite and the integration commands from the technical spec.
- [ ] **[Doc]**       Update README.md and CHANGELOG.md for the scripts' new repository targeting.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-09] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-09] **[Decide]**
  User decided on 2026-11-09 that these scripts stay uninstalled; acting on the current directory's repository removes any need to copy them.
