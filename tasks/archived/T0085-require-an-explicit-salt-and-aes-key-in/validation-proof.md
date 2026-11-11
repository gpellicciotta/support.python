# T0085 validation proof

## Red phase
Command: `pytest tests/test_crypto.py -q` (before implementation)
```
FAILED test_decrypt_property_value_rejects_invalid_key
FAILED test_decrypt_property_value_requires_key
FAILED test_fixed_salt_and_key_constants_removed
FAILED test_standard_password_hash_requires_salt
FAILED test_standard_password_hash_rejects_invalid_salt
5 failed, 4 passed, 1 skipped
```
Recorded vector (current code, explicit salt): `open sesame` -> `0102...1f20:d652eea0c42b0a47...63c69c9f`; it still passes after the change.

## Green phase
`scripts/devops.py check` could not run: the worktree has no `.venv`
(`Virtual environment missing ... run scripts/bootstrap-dev-environment.py first`).
Ran the equivalent steps with the main checkout's venv instead:
```
ruff check .          -> All checks passed!
ruff format --check . -> 165 files already formatted
pytest -q             -> 1110 passed, 4 skipped, 181 subtests passed
lint-markdown check --offline -> 7 issues, all in tests/fixtures/agent_digest (unresolvable relative links in the frozen snapshot); none in changed files
```
The build step of `check` was not run. `test_decrypt_property_value_aes` skipped: `cryptography` is not installed in that venv.
