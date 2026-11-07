### Declared Files
- src/support_python/markdown/__init__.py
- src/support_python/markdown/registry.py
- src/support_python/markdown/rules.py
- src/support_python/markdown/profiles.py
- src/support_python/markdown_lint.py
- src/support_python/cli.py
- tests/test_markdown_lint.py
- tests/test_markdown_profiles.py
- docs/markdown-lint.md
- CHANGELOG.md

### Tests
- Unit: each rule class has a case triggering it and one not triggering it, with unchanged rule IDs and messages.
- Unit: profile loading handles the default profile, the dev-guidelines profile, a missing file, and an unknown rule ID.
- Integration: linting dev-guidelines with the `dev-guidelines` profile prints the same issues as T0014's output.

Completion check: `python -m pytest tests -q`
