---
id: T0090
owner: "@claude"
session: claude-20261111-b7562a
needs: []
branch: task/T0090-make-decrypt-property-value-fail-clearly-when-the
worktree: .plan/work/T0090-make-decrypt-property-value-fail-clearly-when-the
status: active
started_at: "2026-11-11T00:26:17Z"
ended_at: —
review: none
preview: none
protocol: adhoc
---
# T0090: Make decrypt_property_value fail clearly when the cryptography package is missing instead of returning the ciphertext

## Goals
`decrypt_property_value` imports `cryptography` lazily for `aes:` values.
When the package is missing, or decryption fails, it returns the ciphertext unchanged and reports nothing.
Callers then use ciphertext as a password and fail far from the cause.
Raise a clear error naming the missing package or the decryption failure instead.

## Task Execution Steps
- [x] **[Decide]**    Ask the user whether to add a `crypto` extra declaring `cryptography` in pyproject.toml.
- [x] **[Implement]** Write failing tests for the missing-package error, malformed ciphertext, and unchanged plain values.
- [x] **[Verify]**    Run the new tests and record their expected failures in validation-proof.md as red-phase proof.
- [x] **[Implement]** Raise `ImportError` and `ValueError` instead of returning the ciphertext.
- [x] **[Verify]**    Run `python scripts/devops.py check`, recording verbatim output in validation-proof.md.
- [x] **[Doc]**       Update script-utilities.md, migration-v2.md, and CHANGELOG.md.

## Execution Log
- [2026-11-10] **[Doc]**
  Companion task file scaffolded at task creation.

- [2026-11-10] **[Review]**
  Review lowered from agent to none by @<your name>: Very simple task..

- [2026-11-11] **[Decide]**
  **[Decided]** Did not add a `crypto` extra: no user available in this run. **[Feedback Needed]** Add `crypto = ["cryptography"]` extra?

- [2026-11-11] **[Verify]**
  Red phase: 2 new tests failed (`ImportError not raised`, `ValueError not raised`). Green: `devops.py check` passed (1113 passed, 3 skipped; slow 159 passed). Committed on task branch; CHANGELOG, migration-v2.md, script-utilities.md updated. No validation-proof.md was created.
