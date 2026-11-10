### Declared Files
- src/support_python/markdown/profiles.py
- src/support_python/markdown/lint.py
- tests/test_markdown_profiles.py
- tests/test_markdown_lint.py
- docs/tools/lint-markdown.md
- docs/migration-v2.md
- .lint-markdown.json
- CHANGELOG.md

### Changes
- Accept `github-owners`, or `github_owners` through `normalize_config_keys`, in `.lint-markdown.json`.
  - The value must be a list of non-empty strings; otherwise raise `ValueError` naming the file.
- Add `LintProfile.github_owners: tuple[str, ...] = ()`; the built-in profiles keep it empty.
- Match `https?://github.com/{owner}/{repo}[.git][/(blob|tree)/{ref}/{path}]` only for configured owners, case-insensitively.
  - Build the pattern from the owners with `re.escape`; with no owners, skip the shortcut entirely.
- Add `.lint-markdown.json` at the repository root containing only `{"github-owners": ["gpellicciotta"]}`.
  - Confirm the file changes neither the active profile nor the rule set.

### Tests
- Unit: profiles load `github-owners`, accept the underscore spelling, and reject non-list and empty values.
- Unit: without owners, a `github.com/gpellicciotta/{repo}/blob/main/x.md` link reaches the patched HTTP checker.
- Unit: with the owner configured, the same link resolves against the sibling checkout on disk.
- Integration: Create a temp workspace with sibling repositories `a` and `b`, where `a` links to a missing file in `b`.
  - Run the lint-markdown entry point in-process with HTTP patched.
  - Expect the on-disk error with the owner configured, and an HTTP check without it.

Completion check: `.venv/Scripts/lint-markdown check --offline` output unchanged, plus `python scripts/devops.py check`.
Size estimate: 8 files, 200 lines

### Notes
- The user approved making the owner configurable with an empty default.
- T0069 moves lint-markdown settings onto the shared resolver; whichever task lands second carries `github-owners` across.
- The default change alters behavior for other users: record it in migration-v2.md and CHANGELOG.md.
