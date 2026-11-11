# Validation Proof

## Walkthrough & Validation

### Red Phase: Failing Tests

Command: `python scripts/devops.py test tests/test_markdown_profiles.py tests/test_markdown_lint.py`
Exit code: 1

```text
[... 42 lines omitted ...]
=========================== short test summary info ===========================
FAILED tests/test_markdown_profiles.py::test_profile_github_owners_loading_and_validation
FAILED tests/test_markdown_lint.py::TestRuleMD018ValidExternalLinks::test_github_link_with_configured_owner_resolves_to_disk
FAILED tests/test_markdown_lint.py::TestRuleMD018ValidExternalLinks::test_github_link_without_configured_owner_reaches_http_checker
FAILED tests/test_markdown_lint.py::TestLintMarkdownGitHubOwnerIntegration::test_lint_markdown_cli_owner_dependent_link_resolution_integration
4 failed, 105 passed in 4.60s
**[ERROR]** Finished devops test in 5.6s with status: failed
```

### Green Phase: Affected Test Suite

Command: `python scripts/devops.py test tests/test_markdown_profiles.py tests/test_markdown_lint.py`
Exit code: 0

```text
Command: C:\Dev-Projects\support.python\.plan\work\T0088-make-lint-markdown-resolve-github-links-to-sibling\.venv\Scripts\python.exe -m pytest -q tests/test_markdown_profiles.py tests/test_markdown_lint.py
Process ID: 75144
........................................................................ [ 66%]
.....................................                                    [100%]
109 passed in 4.20s
```

### Green Phase: Offline Check Output Unchanged

Command: `.venv/Scripts/lint-markdown check --offline`
Exit code: 1

```text
tests\fixtures\agent_digest\guidelines\general-guidelines.md:53:113: MD014 [valid-relative-links] Relative link '../../plan/src/plan/skills/plan-task-usage-guidelines/SKILL.md' does not resolve to an existing file on disk
tests\fixtures\agent_digest\guidelines\general-guidelines.md:54:105: MD014 [valid-relative-links] Relative link '../../plan/src/plan/skills/research-guidelines/SKILL.md' does not resolve to an existing file on disk
tests\fixtures\agent_digest\guidelines\markdown-guidelines.md:16:59: MD014 [valid-relative-links] Relative link '../scripts/lint-markdown.py' does not resolve to an existing file on disk
tests\fixtures\agent_digest\guidelines\markdown-guidelines.md:61:86: MD014 [valid-relative-links] Relative link '../scripts/lint-markdown.py' does not resolve to an existing file on disk
tests\fixtures\agent_digest\guidelines\markdown-guidelines.md:82:39: MD014 [valid-relative-links] Relative link '../../plan/src/plan/skills/plan-task-usage-guidelines/SKILL.md' does not resolve to an existing file on disk
tests\fixtures\agent_digest\guidelines\markdown-guidelines.md:84:101: MD014 [valid-relative-links] Relative link '../../plan/src/plan/skills/plan-task-usage-guidelines/SKILL.md' does not resolve to an existing file on disk
tests\fixtures\agent_digest\guidelines\ui-guidelines.md:14:40: MD014 [valid-relative-links] Relative link '../docs/notes/visual-design-system-notes.md' does not resolve to an existing file on disk
**[WARN]**  Found 7 lint issues across 58 files.
**[ERROR]** Finished lint-markdown check in 0.9s with status: failed
```

### Green Phase: Full DevOps Verification

Command: `python scripts/devops.py check`
Exit code: 0

```text
Command: C:\Dev-Projects\support.python\.plan\work\T0088-make-lint-markdown-resolve-github-links-to-sibling\.venv\Scripts\python.exe -m ruff check .
Process ID: 41900
All checks passed!
Command: C:\Dev-Projects\support.python\.plan\work\T0088-make-lint-markdown-resolve-github-links-to-sibling\.venv\Scripts\python.exe -m ruff format --check .
Process ID: 73592
165 files already formatted
Command: C:\Dev-Projects\support.python\.plan\work\T0088-make-lint-markdown-resolve-github-links-to-sibling\.venv\Scripts\python.exe -m pytest -q
Process ID: 9676
[... 20 lines omitted ...]
1243 passed, 3 skipped, 206 subtests passed in 322.62s (0:05:22)
Removing dist
Command: C:\Dev-Projects\support.python\.plan\work\T0088-make-lint-markdown-resolve-github-links-to-sibling\.venv\Scripts\python.exe -m build -o dist
Process ID: 25676
[... 315 lines omitted ...]
Successfully built support_python-2.0.17rc0.tar.gz and support_python-2.0.17rc0-py3-none-any.whl
```
