### Declared Files
- src/support_python/crypto.py
- tests/test_crypto.py
- docs/tutorials/script-utilities.md
- docs/migration-v2.md
- CHANGELOG.md
- pyproject.toml (only if the user approves a `crypto` extra)

### Changes
- For an `aes:` value without `cryptography`, raise `ImportError` naming the package and, if added, the extra.
- For a ciphertext that fails to decode, decrypt, or unpad, raise `ValueError`.
- Keep `plain:` and raw values unchanged.
- **[Feedback Needed]** Adding an extra needs the user's approval under the no-new-dependency rule.

### Tests
- Unit: with the `cryptography` import patched to fail, an `aes:` value raises `ImportError` naming the package.
- Unit: a malformed ciphertext raises `ValueError`; `plain:` and raw values behave as before.
- Integration: round-trip an `aes:` value encrypted in the test with an installed `cryptography`, skipped when it is absent.

Completion check: `.venv/Scripts/python -m pytest tests/test_crypto.py` plus `python scripts/devops.py check`.
Size estimate: 6 files, 120 lines

### Notes
- Found during the 2026-11-10 review of project-specific code; needs T0085, which changes the same function's signature.
