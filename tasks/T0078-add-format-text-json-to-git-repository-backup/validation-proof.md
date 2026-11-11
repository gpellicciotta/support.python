# T0078 Validation Proof

## Walkthrough & Validation

## Red phase
Command: `python -m pytest tests/tools/test_git_repository_backup.py -k "JsonFormat or JsonArchive" -m "" -q --timeout=300 -p no:randomly`

Result before implementation: `9 failed, 2 passed`.
Representative failures:
- `AssertionError: 2 != 0 : **[ERROR]** unrecognized arguments: --format json`
- `AssertionError: 2 != 0 : **[ERROR]** unrecognized arguments: --format text`
- `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`

## Green phase
- `python -m pytest -q` (fast suite): `1200 passed, 5 skipped, 181 subtests passed in 13.44s`.
- `python -m pytest -m slow -q --timeout=300 tests/tools/test_git_repository_backup.py`: `64 passed, 26 subtests passed in 17.08s`.
- `python -m ruff check src tests`: `All checks passed!`; `ruff format --check`: `130 files already formatted`.
- `lint-markdown check --offline`: 7 issues, all in `tests/fixtures/agent_digest/` (frozen snapshot, unresolved sibling links); none in changed files.
- The worktree has no `.venv`, so checks ran with system Python and `PYTHONPATH=src`.

## Terminal output
```text
$ python -m pytest tests/tools/test_git_repository_backup.py -k "JsonFormat or JsonArchive" -m "" -q   (before implementation)
FAILED ...TestBackupJsonFormat::test_reports_one_mirror_entry_per_repo   AssertionError: 2 != 0 : **[ERROR]** unrecognized arguments: --format json
9 failed, 2 passed

$ python -m pytest -q   (after implementation)
1200 passed, 5 skipped, 181 subtests passed in 13.44s

$ python -m pytest -m slow -q --timeout=300 tests/tools/test_git_repository_backup.py
64 passed, 26 subtests passed in 17.08s
```
