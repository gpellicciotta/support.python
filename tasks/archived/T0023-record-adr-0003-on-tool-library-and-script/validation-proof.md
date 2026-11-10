### Verification Evidence

- Offline Markdown Linter on `docs`, `CHANGELOG.md`, and `CLAUDE.md` (run from worktree with `PYTHONPATH=src` using the primary checkout `.venv`):
  - Command: `$env:PYTHONPATH="src"; {{project-root}}/.venv/Scripts/support-python.exe lint markdown check --offline docs CHANGELOG.md CLAUDE.md`
  - Exit Code: `0`
  - Output:
    ```text
    Starting lint-markdown v2.0.0-pre+4834dae with configuration:
    - Command: check
    - Log file: none
    - Log level: INFO
    - Verbose: false
    - Working directory: {{project-root}}/.plan/work/T0023-record-adr-0003-on-tool-library-and-script
    All 10 markdown files passed linting.
    Finished lint-markdown check in 0.4s with status: succeeded
    ```

- Automated Test Suite (run from worktree using the primary checkout `.venv`):
  - Command: `{{project-root}}/.venv/Scripts/python.exe -m pytest -q`
  - Exit Code: `0`
  - Output:
    ```text
    ............................................................ [  8%]
    .............................................................. [ 16%]
    ................................................ [ 23%]
    ........................................................ [ 30%]
    ........................................................................ [ 40%]
    ................................s....................................... [ 50%]
    .............................................s......s................... [ 59%]
    ........................................................................ [ 69%]
    ...................................................................... [ 79%]
    ........................................................................ [ 89%]
    ........................................................................ [ 98%]
    .........                                                                [100%]
    734 passed, 3 skipped, 64 subtests passed in 146.74s (0:02:26)
    ```
