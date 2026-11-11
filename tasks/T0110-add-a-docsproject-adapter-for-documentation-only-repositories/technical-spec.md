# Documentation Project Adapter
## Technical Specifications
Expose DocsProject through support_python.devops, using the existing changelog-only version and release pipeline.
Resolve lint-markdown on PATH and run check/fix with --offline at the repository root.
Skip tests, slow tests, builds, and cleanup without creating artifacts.
Keep support.webapp unchanged; its adapter provides the behavior reference for this reusable implementation.
### Declared Files
- src/support_python/devops/projects.py
- src/support_python/devops/__init__.py
- tests/test_devops_projects_docs.py
- tests/test_devops.py
- tests/test_devops_versions.py
- docs/devops.md
- CHANGELOG.md
### Tests
- Unit: Verify command arguments, root forwarding, missing executables, failures, skipped operations, exports, and changelog-only versions.
- Integration: Run a real DocsProject entry point with lint-markdown against valid and invalid temporary Markdown repositories.
- Integration: Verify changelog-only release dry-run planning and skip flags without outbound operations.
Completion check: Run affected adapter, version, export, and release tests, plus Ruff and offline Markdown lint.
Size estimate: 7 files, 250 lines
