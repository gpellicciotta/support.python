### Declared Files
- src/support_python/crypto.py
- src/support_python/__init__.py
- tests/test_crypto.py
- docs/tutorials/script-utilities.md
- docs/migration-v2.md
- CHANGELOG.md

### Changes
- `get_standard_password_hash(password: str, salt: bytes) -> str`: both arguments are required.
  - Keep PBKDF2-HMAC-SHA1, 20,000 iterations, a 32-byte key, and the `hex(salt):hex(hash)` format.
  - Raise `ValueError` for an empty salt.
- `decrypt_property_value(val: Optional[str], key_hex: str) -> str`: `key_hex` is required.
  - Raise `ValueError` unless `key_hex` has 32, 48, or 64 hexadecimal digits.
  - Keep the `plain:` and raw-value handling unchanged.
- Remove `STANDARD_SALT` and `DEFAULT_AES_KEY_HEX` from `crypto.py`, its `__all__`, and the package root.
- **[Decided]** Keep `DEFAULT_TEST_PASSWORD`; it is a test value, not a secret, and outside the approved scope.

### Tests
- Unit: omitting `salt` or `key_hex` raises `TypeError`; an empty salt and malformed keys raise `ValueError`.
- Unit: a hash computed with the old salt passed explicitly equals the vector recorded before the change.
- Unit: the removed constants are absent from `support_python` and `support_python.crypto`.
- Integration test: none (pure functions without I/O; `aes:` decryption needs the uninstalled `cryptography`, see T0090).

Completion check: `.venv/Scripts/python -m pytest tests/test_crypto.py` plus `python scripts/devops.py check`.
Size estimate: 6 files, 150 lines

### Notes
- Needs T0084, which removes the last internal use of the default salt in `sql.py`.
- counters.server re-exports `STANDARD_SALT` and calls `decrypt_property_value` without a key; auth hashes with the default salt.
- Both pin support-python v1.0.0; their backlog tasks cover passing these values explicitly on upgrade.
- Breaking v2 change: record it in both migration-v2.md and CHANGELOG.md.
