## Walkthrough & Validation

### Red phase
`.venv/Scripts/python -m pytest -q tests/test_cli.py -k "option_label or column"` (exit 1, before the fix):
```text
=========================== short test summary info ===========================
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_long_action_option_label_keeps_aligned_separated_columns
FAILED tests/test_cli.py::ToolHarnessUnitTests::test_long_global_option_label_keeps_aligned_separated_columns
2 failed, 1 passed, 10 deselected in 0.43s
```

### Green phase
`.venv/Scripts/python -m pytest -q` (exit 0):
```text
1054 passed, 3 skipped, 133 subtests passed in 118.79s (0:01:58)
```

`.venv/Scripts/ruff check .` and `.venv/Scripts/ruff format --check .` (exit 0):
```text
All checks passed!
156 files already formatted
```

### Integration
`.venv/Scripts/agent-files help` Options excerpt (exit 0):
```text
Options:
  -h, --help              show help message and exit
  --version               show version information and exit
  -v, --verbose           enable verbose output logging
  --debug                 enable debug output logging
  --log-file PATH         append operational logs to specified file
  --log-level LEVEL       logging severity threshold (DEBUG, INFO, WARN, ERROR; default: INFO)
  --config PATH           path to .agent-files.json configuration file
  --repo-root PATH        repository root directory override
  --digest PATH           digest file to install (default: ./agent-digest.md)
  --skills-dir PATH       skills directory to install (default: ./agent-skills)
  --marker NAME           guarded block marker identifier override
  --marker-begin TEXT     guarded block begin marker line override
  --marker-end TEXT       guarded block end marker line override
  --manifest-source NAME  skills ownership manifest source name override
  --legacy-skill NAME     replace legacy_skill_names with bootstrap skill name (repeatable)
  --dry-run               report what sync would change without writing or deleting anything
  --no-prune              keep stale skills and stale skill files on sync, reporting them only
  --timeout SECONDS       per-tool timeout in seconds for review (default: 900)

```
