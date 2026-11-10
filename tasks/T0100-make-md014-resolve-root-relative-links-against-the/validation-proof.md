## Walkthrough & Validation

Red phase in GitHub CI, run 42843923273 on Linux (Python 3.x):
```text
$ pytest -q
_ TestDiscoverMarkdownFilesGitIgnore.test_root_relative_link_resolves_against_project_root _
self = <tests.test_markdown_lint.TestDiscoverMarkdownFilesGitIgnore testMethod=test_root_relative_link_resolves_against_project_root>
    def test_root_relative_link_resolves_against_project_root(self) -> None:
E           AssertionError: 0 != 1
exit=1
```

Red phase locally, with the POSIX simulation test:
```text
$ .venv/Scripts/python -m pytest -q tests/test_markdown_lint.py -k root_relative
=========================== short test summary info ===========================
FAILED tests/test_markdown_lint.py::TestDiscoverMarkdownFilesGitIgnore::test_root_relative_link_resolves_where_a_leading_slash_is_absolute
1 failed, 1 passed, 91 deselected in 0.45s
exit=1
```

Green phase locally:
```text
$ python scripts/devops.py check
All checks passed!
1207 passed, 3 skipped, 191 subtests passed in 129.78s (0:02:09)
Successfully built support_python-2.0.7rc0.tar.gz and support_python-2.0.7rc0-py3-none-any.whl
exit=0
```
