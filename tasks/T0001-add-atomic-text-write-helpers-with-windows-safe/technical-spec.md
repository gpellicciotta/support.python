### Declared Files
- src/support_python/files.py
- tests/test_files.py
- src/support_python/__init__.py
- CHANGELOG.md
- README.md
- CLAUDE.md
- docs/index.md

Size estimate: 7 files, 350 lines

**[Estimation]** Based on the line counts of the source functions in the sibling project.

### Tests
- Unit: atomic_write_text creates a missing file and overwrites an existing one with the exact content.
- Unit: atomic_write_text leaves no temporary file behind when the write raises; the original file stays intact.
- Unit: atomic_write_text keeps the permission bits of the replaced file (POSIX only; skipped on Windows).
- Unit: The temporary file name omits the target name, so a long target name cannot exceed the path limit.
- Unit: The newline argument controls newline translation.
- Unit: atomic_replace retries on PermissionError and winerror 5/32 (patched Path.replace), then succeeds.
- Unit: atomic_replace raises after max_retries and still removes the source file.
- Unit: read_text_retrying retries on PermissionError, then returns; errors='strict' raises on undecodable bytes.
- Integration: A writer thread loops atomic_write_text with alternating long contents while a reader thread loops read_text_retrying; the reader never sees partial or mixed content.

Completion check: python -m pytest tests/test_files.py && ruff check . && ruff format --check .

### Decisions
- **[Decided]** Merge replace_with_text into atomic_write_text; the write-journal comment in plan is plan-specific.
- **[Decided]** New module is files.py, exported from the package root like the other modules.
