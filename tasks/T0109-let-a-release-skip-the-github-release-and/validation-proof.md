# Validation Proof

## Walkthrough & Validation
Command: `plan tasks validate T0109 --completion`

Exit code: 0
```text
All 1 task file passed validation.
```

Red phase command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m pytest tests/test_devops_cli.py tests/test_devops_projects_gradle.py tests/test_devops_release_pipeline.py -m 'slow or not slow' -n 0 -q --timeout=120`

Exit code: 1. Verbatim final summary:
```text
5 failed, 112 passed, 17 subtests passed in 39.11s
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m pytest tests/test_devops_cli.py tests/test_devops_projects_gradle.py tests/test_devops_release_pipeline.py -m 'slow or not slow' -n 4 -q --timeout=120`

Exit code: 0
```text
bringing up nodes...
bringing up nodes...

................u...u.u.u...u..........................u..u.u.u.......uu [ 52%]
..uuu..u......uu...............................................          [100%]
118 passed, 17 subtests passed in 13.98s
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m ruff check src/support_python/devops tests/test_devops_cli.py tests/test_devops_projects_gradle.py tests/test_devops_release_pipeline.py scripts/devops.py`

Exit code: 0
```text
All checks passed!
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe -m ruff format --check src/support_python/devops tests/test_devops_cli.py tests/test_devops_projects_gradle.py tests/test_devops_release_pipeline.py scripts/devops.py`

Exit code: 0
```text
12 files already formatted
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/python.exe scripts/devops.py release --help`

Exit code: 0
```text
devops v3.2.0-pre+cff52f6 - Copyright (c) Giovanni Pellicciotta

Detailed Action Description: release
  Release the project with ReleasePipeline after running `check` as its quality check.
  The project is rebuilt after the version freeze, and those outputs are attached to the GitHub release.
  A project with its own release, such as a GradleProject with a release_task, runs that instead.

Examples:
  devops release --dry-run

Usage:
  devops release [--dry-run] [--skip-checks] [--skip-github-release] [--yes]

Options:
  -h, --help             show help message and exit
  --version              show version information and exit
  -v, --verbose          enable verbose output logging
  --debug                enable debug output logging (implies --verbose)
  --log-file PATH        append operational logs to specified file
  --log-level LEVEL      logging severity threshold (DEBUG, INFO, WARN, ERROR; default: INFO)
  --dry-run              log the planned steps without changing anything
  --skip-checks          skip the `check` quality check
  --skip-github-release  skip GitHub release creation and gh checks
  --yes                  skip the typed confirmation

Exit codes:
  0   success
  1   an operation failed, a prerequisite is missing, or versions drift
  2   invalid arguments or unknown action
```

Command: `C:/Dev-Projects/support.python/.venv/Scripts/lint-markdown.exe check --offline CHANGELOG.md docs/devops.md docs/tutorials/devops-scripts.md`

Exit code: 0
```text
All 3 markdown files passed linting.
```

The work loop owns full-suite verification. Affected tests include temporary Git origin pushes and actual CLI help execution.

