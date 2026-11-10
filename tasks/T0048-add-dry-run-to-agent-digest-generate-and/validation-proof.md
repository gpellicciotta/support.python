## Walkthrough & Validation

### Red phase
`.venv/Scripts/python -m pytest -q tests/tools/test_agent_digest.py -k "DryRun or JsonFormat"` (exit 1, before the implementation):
```text
=========================== short test summary info ===========================
FAILED tests/tools/test_agent_digest.py::TestGenerateDryRun::test_dry_run_appears_in_startup_banner
FAILED tests/tools/test_agent_digest.py::TestGenerateDryRun::test_dry_run_on_fresh_sources_writes_nothing
FAILED tests/tools/test_agent_digest.py::TestGenerateDryRun::test_dry_run_reports_up_to_date_then_would_update
FAILED tests/tools/test_agent_digest.py::TestGenerateDryRun::test_dry_run_still_enforces_byte_budget
FAILED tests/tools/test_agent_digest.py::TestCheckJsonFormat::test_failures_become_issues
FAILED tests/tools/test_agent_digest.py::TestCheckJsonFormat::test_fresh_output_reports_ok_document
FAILED tests/tools/test_agent_digest.py::TestCheckJsonFormat::test_missing_path_exits_two_with_empty_stdout
FAILED tests/tools/test_agent_digest.py::TestCheckJsonFormat::test_text_format_prints_no_json
8 failed, 26 deselected in 0.79s
```

### Green phase
`.venv/Scripts/python -m pytest -q` (exit 0):
```text
1075 passed, 3 skipped, 138 subtests passed in 119.41s (0:01:59)
```

`.venv/Scripts/ruff check .` and `.venv/Scripts/ruff format --check .` (exit 0):
```text
All checks passed!
156 files already formatted
```

### Installed integration checks
Run in a copy of `tests/fixtures/agent_digest` with a `.git` marker.
`agent-digest check guidelines --digest guidelines/agent-digest.md --skills-dir skills --link-base {{dev-guidelines-blob-url}} --format json --verbose`:
```text
exit=0; json.load(stdout): ok=True digest.status=up-to-date skills=12 issues=0
stderr banners:
Starting agent-digest v2.0.40-pre+43df589 with configuration:
Finished agent-digest check in 0.1s with status: succeeded
```

`agent-digest generate guidelines --digest out.md --skills-dir out --dry-run`:
```text
exit=0; out.md exists=no; out/ exists=no
Would create out/change-management-guidelines/SKILL.md (71 lines).
Would create out/cli-guidelines/SKILL.md (34 lines).
Would create out/database-guidelines/SKILL.md (22 lines).
...
Would create out.md (184 lines, 12577 bytes).
```

Both scenarios are also automated in `TestGenerateAgentDigestEndToEnd` against the installed console script.
