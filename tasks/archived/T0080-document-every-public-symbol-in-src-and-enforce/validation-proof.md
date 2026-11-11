# T0080 validation proof

## Red phase
Baseline `ruff check src --select D1`: 72 findings (task text said 70).
After enabling D100-D107 in pyproject.toml, `ruff check .`: `Found 72 errors.`

## Green phase
`ruff check .`:
```text
All checks passed!
```
`ruff format --check .`: `171 files already formatted`

`python -m pytest -q` (fast suite):
```text
1200 passed, 5 skipped, 181 subtests passed in 14.53s
```
