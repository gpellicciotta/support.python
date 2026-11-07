## Walkthrough & Validation

### Key Changes
- Copied dev-guidelines `scripts/update-global-agent-files.py` into `src/support_python/agent_files.py` and fixed imports to use `support_python.cli.PROJECT_VERSION`, `support_python.cli.ToolHarness`, and `support_python.logging`.
- Added `find_project_root`, `_resolve_repo_root`, `_resolve_digest_path`, and `_resolve_skills_dir` so `REPO_ROOT`, `DIGEST_PATH`, `SKILLS_DIR`, and `scripts/generate-agent-digest.py` resolve dynamically from the current working directory's repository root when unpatched, while honoring module-attribute patches in tests.
- Defined `ToolLogger` (`TeeLogger` alias) in `agent_files.py` routing `WARN` and `ERROR` messages logged via `.log()` to `stderr`, matching `dev-guidelines` `tool_common.ToolLogger`.
- Aliased `sync` to `update` and `check` to `diff` in `SyncHarness.run`, and moved UTF-8 stream reconfiguration into `agent_files.main()`.
- Copied dev-guidelines `scripts/tests/test_update_global_agent_files.py` into `tests/test_agent_files.py`, updated imports, and added `RepoRootResolutionTests` and `SupportPythonAgentFilesCliTests`.
- Registered `agent-files` in `src/support_python/cli.py` (`support-python agent-files list|sync|check|review`) and added a module-directory fallback for `PROJECT_VERSION`.
- Documented `support-python agent-files` in `README.md`, `docs/index.md`, and `CHANGELOG.md` (bumping to `v1.0.21-pre` in `CHANGELOG.md` and `pyproject.toml`).

### Red-Phase Test Failure Proof
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/test_agent_files.py -q`
Exit code: `1`
```text
............................................................ [ 68%]
..........................F                                              [100%]
[... 88 lines omitted ...]
---------------------------- Captured stderr call -----------------------------
usage: support-python [-h] [-v] [--verbose] [--debug]
                      [{greet,backup,lint,version,help}] [name]
support-python: error: argument action: invalid choice: 'agent-files' (choose from greet, backup, lint, version, help)
=========================== short test summary info ===========================
FAILED tests/test_agent_files.py::SupportPythonAgentFilesCliTests::test_support_python_agent_files_subcommands_dispatch
1 failed, 86 passed, 12 subtests passed in 2.79s
```

### Green-Phase Test Suite and Linter Verification
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests/test_agent_files.py -q`
Exit code: `0`
```text
............................................................ [ 68%]
...........................                                              [100%]
87 passed, 12 subtests passed in 2.45s
```

Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest tests -q`
Exit code: `0`
```text
............................................................ [  8%]
.............................................................. [ 16%]
........................................................................................................ [ 30%]
........................................................................ [ 40%]
........................s............................................... [ 49%]
..............................................................s......s.. [ 59%]
........................................................................ [ 69%]
...................................................................... [ 78%]
........................................................................ [ 88%]
........................................................................ [ 97%]
................                                                         [100%]
741 passed, 3 skipped, 64 subtests passed in 166.47s (0:02:46)
```

Command: `python scripts/update-global-agent-files.py update --dry-run` (in `C:\Dev-Projects\dev-guidelines`)
Exit code: `1`
```text
Starting update-global-agent-files v1.12.9-pre+5f5408e with configuration:
- Command: update
- Log file: none
- Log level: INFO
- Verbose: false
- Tools selected: claude-code, antigravity, codex-cli
- Dry run: true
- Prune stale skills: true
<claude-code> diff: pending changes --
[... 201 lines omitted ...]
<codex-cli> diff: skill 'process-management-guidelines' pending changes --
              content mismatch: SKILL.md
<codex-cli> diff: skill 'python-guidelines' pending changes --
              content mismatch: SKILL.md
<codex-cli> diff: skill 'testing-guidelines' pending changes --
              content mismatch: SKILL.md
<codex-cli> stale skill 'plan-task-usage-guidelines' would be removed
<codex-cli> stale skill 'research-guidelines' would be removed
**[ERROR]** Finished update-global-agent-files update in 0.4s with status: failed
```

Command: `python -c "import sys; from support_python.cli import main; sys.exit(main(sys.argv[1:]))" agent-files sync --dry-run` (in `C:\Dev-Projects\dev-guidelines`)
Exit code: `1`
```text
Starting update-global-agent-files v1.0.21-pre+d9f4c53 with configuration:
- Command: update
- Log file: none
- Log level: INFO
- Verbose: false
- Tools selected: claude-code, antigravity, codex-cli
- Dry run: true
- Prune stale skills: true
<claude-code> diff: pending changes --
[... 201 lines omitted ...]
<codex-cli> diff: skill 'process-management-guidelines' pending changes --
              content mismatch: SKILL.md
<codex-cli> diff: skill 'python-guidelines' pending changes --
              content mismatch: SKILL.md
<codex-cli> diff: skill 'testing-guidelines' pending changes --
              content mismatch: SKILL.md
<codex-cli> stale skill 'plan-task-usage-guidelines' would be removed
<codex-cli> stale skill 'research-guidelines' would be removed
**[ERROR]** Finished update-global-agent-files update in 0.3s with status: failed
```

Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m ruff check . ; C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m ruff format --check .`
Exit code: `0`
```text
All checks passed!
83 files already formatted
```
