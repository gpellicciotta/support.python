# T0091 Validation Proof

## Walkthrough & Validation
### Failing Tests Before the Implementation
```text
$ python scripts/devops.py test tests/test_devops_projects_gradle.py tests/test_devops_cli.py tests/test_devops_projects_node.py
E       AssertionError: 'tests/test_cli.py' unexpectedly found in 'devops v2.0.1-pre - Copyright (c) Giovanni Pellicciotta ...
E       AssertionError: 'doFullRelease' not found in '  release                freeze, tag, push, publish a GitHub release, and reopen development'
E       AssertionError: 'ktlintCheck' not found in '  lint                   check lint and formatting without changing files'
E       AssertionError: 'spotlessCheck checkstyleMain checkstyleTest' not found in '  lint                   check lint and formatting without changing files'
E       AssertionError: '--skip-checks' not found in ''
E       AssertionError: 'tests/test_cli.py' unexpectedly found in 'devops v2.0.1-pre - Copyright (c) Giovanni Pellicciotta ...
FAILED tests/test_devops_projects_gradle.py::GradleHelpTests::test_help_examples_use_a_gradle_test_filter
FAILED tests/test_devops_projects_gradle.py::GradleHelpTests::test_help_release_summary_names_the_release_task
FAILED tests/test_devops_projects_gradle.py::GradleHelpTests::test_help_summaries_follow_task_list_overrides
FAILED tests/test_devops_projects_gradle.py::GradleHelpTests::test_help_summaries_name_the_gradle_tasks_of_each_action
FAILED tests/test_devops_projects_gradle.py::GradleHelpTests::test_skip_checks_with_a_release_task_warns_that_it_is_ignored
FAILED tests/test_devops_projects_node.py::NodeReleaseTests::test_help_examples_use_an_npm_test_selection
6 failed, 85 passed, 24 subtests passed in 4.16s
exit 1
```

The two new Python tests passed before and after: they guard the unchanged Python help.

### Tests After the Implementation
```text
$ python scripts/devops.py test tests/test_devops_projects_gradle.py tests/test_devops_cli.py tests/test_devops_projects_node.py
91 passed, 24 subtests passed in 4.77s
exit 0

$ python scripts/devops.py check
Command: C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m ruff check .
All checks passed!
Command: C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m ruff format --check .
162 files already formatted
Command: C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest -q
1192 passed, 3 skipped, 189 subtests passed in 136.37s (0:02:16)
Command: C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m build -o dist
Successfully built support_python-2.0.1rc0.tar.gz and support_python-2.0.1rc0-py3-none-any.whl
exit 0
```

### Integration: GradleProject Help in template.java
Ran `DevopsCli(GradleProject(template.java, release_task="doFullRelease"))` from `src/` with `help --verbose`:

```text
Actions:
  lint                   check lint and formatting: gradle spotlessCheck checkstyleMain checkstyleTest
  format                 reformat the sources in place: gradle spotlessApply
  test                   run the tests, adding --tests per selection item: gradle test
  build                  build the outputs: gradle build
  check                  run lint, test, and build: gradle build
  clean                  remove build outputs: gradle clean
  versions               compare the version file with the CHANGELOG.md top heading
  release                confirm, then release with the Gradle task doFullRelease
```

### Review Rework
Agent review approved with five low findings. Fixed: "(default tasks)" for empty lists, a neutral `check` summary, the weak test, and documented build-time reads.
The integration snapshot above predates the rework; `check` now reads "run the full check: gradle build".
Accepted: the `--skip-checks` warning logs after the release returns. Follow-up: Python-specific exit-code text.

```text
$ python scripts/devops.py check   -> exit 0
All checks passed!
162 files already formatted
1193 passed, 3 skipped, 189 subtests passed in 131.74s (0:02:11)
Successfully built support_python-2.0.1rc0.tar.gz and support_python-2.0.1rc0-py3-none-any.whl
```
