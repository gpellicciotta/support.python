---
id: T0085
owner: "@claude"
session: claude-20261111-9f764f
needs: []
branch: task/T0085-require-an-explicit-salt-and-aes-key-in
worktree: .plan/work/T0085-require-an-explicit-salt-and-aes-key-in
status: active
started_at: "2026-11-11T00:23:08Z"
ended_at: —
review: none
preview: none
protocol: adhoc
usage:
  worker: {turns: 2, duration_s: 227.0, input: 64, output: 19238, cache_read: 1478528, cache_write: 79586}
work_duration: 125.6
---
# T0085: Require an explicit salt and AES key in the crypto helpers, removing STANDARD_SALT and DEFAULT_AES_KEY_HEX

## Goals
`crypto.py` ships a fixed salt matching support.java and a hardcoded AES key as public defaults.
Any caller that omits them silently shares those values with every other caller.
Remove `STANDARD_SALT` and `DEFAULT_AES_KEY_HEX`, and make the salt and the key required arguments.
Hashes and decryptions computed with explicitly passed values must stay identical to today's.

## Task Execution Steps
- [x] **[Read]**      Read crypto.py, test_crypto.py, and the crypto section of script-utilities.md.
- [x] **[Implement]** Record a hash vector from the current code, then write failing tests for the required arguments.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Make salt and key required, validate them, and remove the two constants from all exports.
- [x] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Update script-utilities.md, migration-v2.md, and CHANGELOG.md.

## Execution Log
- [2026-11-11] **[Verify]**
  Red-phase and green-phase evidence is in validation-proof.md; devops check could not run in the worktree (no .venv), so ruff, pytest, and lint-markdown ran with the main venv. Build step not run.

- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Review lowered from agent to none by @<your name>: Very simple task..

- [2026-11-11] **[Verify]**
  Completion validation found 1 errors; pending fix turn 1 of 2.
  - TF020.

- [2026-11-11] **[Read]**
  Read crypto.py, test_crypto.py, and the script-utilities.md crypto section.

- [2026-11-11] **[Implement]**
  Recorded the hash vector and wrote failing tests for required salt and key.

- [2026-11-11] **[Verify]**
  Red phase: 5 new tests failed as expected; recorded in validation-proof.md.

- [2026-11-11] **[Implement]**
  Made salt keyword-only and key required, validated both, removed the constants from exports.

- [2026-11-11] **[Doc]**
  Updated script-utilities.md, sql-anonymizer.md, migration-v2.md, and CHANGELOG.md.

