## Walkthrough & Validation

Command: `python -m pytest tests/test_git.py -q` (exit code 1, before implementation).

```text
E   ImportError: cannot import name 'git' from 'support_python' (C:\Dev-Projects\support.python\src\support_python\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_git.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.44s
```

Command: `python -m pytest tests/test_git.py -q` (exit code 0).

```text
...........................................                              [100%]
43 passed in 1.44s
```

Command: `ruff check .` (exit code 0).

```text
All checks passed!
```

Command: `ruff format --check .` (exit code 0).

```text
63 files already formatted
```

Command: `python ../dev-guidelines/scripts/lint-markdown.py check README.md CLAUDE.md CHANGELOG.md docs/index.md --offline` (exit code 1).

```text
[... 2 lines omitted ...]
- Log file: none
- Log level: INFO
- Verbose: false
- Working directory: C:\Dev-Projects\support.python
CHANGELOG.md:15:1: MD015 [no-blank-line-after-subheading] Heading 'v1.0.2-pre' (H2) must not be followed by a blank line before content
CHANGELOG.md:22:1: MD015 [no-blank-line-after-subheading] Heading 'v1.0.0 [released: 2026-10-31]' (H2) must not be followed by a blank line before content
CLAUDE.md:11:1: MD015 [no-blank-line-after-subheading] Heading 'What this is' (H2) must not be followed by a blank line before content
CLAUDE.md:21:1: MD015 [no-blank-line-after-subheading] Heading 'Commands' (H2) must not be followed by a blank line before content
CLAUDE.md:36:1: MD015 [no-blank-line-after-subheading] Heading 'Architecture' (H2) must not be followed by a blank line before content
CLAUDE.md:38:1: MD016 [no-blank-line-before-list] Sentence introducing a list must not be followed by a blank line
CLAUDE.md:51:8: MD019 [file-references-as-links] Repository file reference 'docs/adrs/ADR-0001-devops-scripts-toolkit-scope.md' in prose must be formatted as markdown link [filename](path)
CLAUDE.md:57:1: MD015 [no-blank-line-after-subheading] Heading 'Development Guidelines' (H2) must not be followed by a blank line before content
CLAUDE.md:60:1: MD016 [no-blank-line-before-list] Sentence introducing a list must not be followed by a blank line
CLAUDE.md:77:1: MD015 [no-blank-line-after-subheading] Heading 'Conventions' (H2) must not be followed by a blank line before content
docs\index.md:7:1: MD015 [no-blank-line-after-subheading] Heading 'Core Documentation' (H2) must not be followed by a blank line before content
docs\index.md:20:1: MD015 [no-blank-line-after-subheading] Heading 'Architectural Decision Records' (H2) must not be followed by a blank line before content
docs\index.md:27:1: MD015 [no-blank-line-after-subheading] Heading 'Guidelines' (H2) must not be followed by a blank line before content
README.md:12:1: MD015 [no-blank-line-after-subheading] Heading 'Bootstrap' (H2) must not be followed by a blank line before content
README.md:22:1: MD015 [no-blank-line-after-subheading] Heading 'Build' (H2) must not be followed by a blank line before content
README.md:31:1: MD019 [file-references-as-links] Repository file reference '.github/workflows/python-package.yml' in prose must be formatted as markdown link [filename](path)
README.md:33:1: MD015 [no-blank-line-after-subheading] Heading 'Install CLI' (H2) must not be followed by a blank line before content
README.md:42:1: MD015 [no-blank-line-after-subheading] Heading 'Use from another Python project' (H2) must not be followed by a blank line before content
README.md:50:1: MD015 [no-blank-line-after-subheading] Heading 'Shared CLI helpers, tabular output, and session storage' (H2) must not be followed by a blank line before content
README.md:104:1: MD015 [no-blank-line-after-subheading] Heading 'Common script utilities' (H2) must not be followed by a blank line before content
README.md:106:1: MD016 [no-blank-line-before-list] Sentence introducing a list must not be followed by a blank line
README.md:141:1: MD015 [no-blank-line-after-subheading] Heading 'CLI logging' (H2) must not be followed by a blank line before content
README.md:157:1: MD015 [no-blank-line-after-subheading] Heading 'REST client HTTP transport' (H2) must not be followed by a blank line before content
README.md:178:1: MD015 [no-blank-line-after-subheading] Heading 'REST client error hierarchy and status mapping' (H2) must not be followed by a blank line before content
README.md:203:1: MD015 [no-blank-line-after-subheading] Heading 'DevOps script helpers and environment managers' (H2) must not be followed by a blank line before content
README.md:236:1: MD015 [no-blank-line-after-subheading] Heading 'View Capture Engine and Static Server' (H2) must not be followed by a blank line before content
README.md:271:1: MD015 [no-blank-line-after-subheading] Heading 'SQL Snapshot Anonymizer' (H2) must not be followed by a blank line before content
README.md:288:1: MD015 [no-blank-line-after-subheading] Heading 'Models and wire helpers' (H2) must not be followed by a blank line before content
README.md:316:1: MD015 [no-blank-line-after-subheading] Heading 'Installation and Releases' (H2) must not be followed by a blank line before content
README.md:320:1: MD015 [no-blank-line-after-subheading] Heading 'Install via Git' (H3) must not be followed by a blank line before content
README.md:336:1: MD015 [no-blank-line-after-subheading] Heading 'GitHub Releases' (H3) must not be followed by a blank line before content
README.md:338:40: MD019 [file-references-as-links] Repository file reference '.github/workflows/publish.yml' in prose must be formatted as markdown link [filename](path)
README.md:341:1: MD015 [no-blank-line-after-subheading] Heading 'Version and dependencies' (H2) must not be followed by a blank line before content
**[WARN]**  Found 33 lint issues across 4 files.
**[ERROR]** Finished lint-markdown check in 0.1s with status: failed
```

Full-suite command: `python -m pytest -q` (exit code 0; execution session 36639).
This run preceded the final parser fix; the targeted suite above verifies the final Git implementation.

```text
427 passed, 50 subtests passed in 68.35s (0:01:08)
```

Markdown baseline counts: README 20, CLAUDE 8, CHANGELOG 2, documentation index 3.
All 33 findings existed before this task; the new documentation introduced no additional findings.
