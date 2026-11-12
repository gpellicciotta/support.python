## Technical Specifications
### Declared Files
- src/support_python/devops/cli.py
- src/support_python/devops/projects.py
- src/support_python/devops/release.py
- tests/test_devops_cli.py
- tests/test_devops_projects_gradle.py
- tests/test_devops_release_pipeline.py
- docs/devops.md
- docs/tutorials/devops-scripts.md
- scripts/devops.py
- CHANGELOG.md

### Tests
- Unit: Verify CLI forwarding and Gradle skip-checks properties for dry and real releases.
- Integration: Run the pipeline against temporary Git repositories without gh; verify tags, pushes, and development reopening.

Completion check: Affected DevOps tests, CLI help, Ruff, and offline Markdown lint.
Size estimate: 10 files, 160 lines

### Behavior
`--skip-github-release` omits gh checks, publication, and the release URL while retaining Git operations and builds.
Project-owned release hooks receive requested skip flags. Gradle receives `-PskipChecks=true` and `-PskipGithubRelease=true`.
Project release tasks must implement these properties.
