---
id: T0090
owner: ~
needs: [T0085]
branch: —
worktree: —
status: ready
started_at: —
ended_at: —
review: agent
preview: none
protocol: standard
---
# T0090: Make decrypt_property_value fail clearly when the cryptography package is missing instead of returning the ciphertext

## Goals
`decrypt_property_value` imports `cryptography` lazily for `aes:` values.
When the package is missing, or decryption fails, it returns the ciphertext unchanged and reports nothing.
Callers then use ciphertext as a password and fail far from the cause.
Raise a clear error naming the missing package or the decryption failure instead.

## Task Execution Steps
- [ ] **[Decide]**    Ask the user whether to add a `crypto` extra declaring `cryptography` in pyproject.toml.
- [ ] **[Implement]** Write failing tests for the missing-package error, malformed ciphertext, and unchanged plain values.
- [ ] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [ ] **[Implement]** Raise `ImportError` and `ValueError` instead of returning the ciphertext.
- [ ] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [ ] **[Doc]**       Update script-utilities.md, migration-v2.md, and CHANGELOG.md.
- [ ] **[Review]**    Obtain review approval of the finished work before completion.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.
