---
id: T0085
owner: ~
needs: [T0084]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0085: Require an explicit salt and AES key in the crypto helpers, removing STANDARD_SALT and DEFAULT_AES_KEY_HEX

## Goals
`crypto.py` ships a fixed salt matching support.java and a hardcoded AES key as public defaults.
Any caller that omits them silently shares those values with every other caller.
Remove `STANDARD_SALT` and `DEFAULT_AES_KEY_HEX`, and make the salt and the key required arguments.
Hashes and decryptions computed with explicitly passed values must stay identical to today's.

## Task Execution Steps
- [ ] **[Read]**      Read crypto.py, test_crypto.py, and the crypto section of script-utilities.md.
- [ ] **[Implement]** Record a hash vector from the current code, then write failing tests for the required arguments.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Make salt and key required, validate them, and remove the two constants from all exports.
- [ ] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Update script-utilities.md, migration-v2.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
