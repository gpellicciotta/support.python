### Task Mapping
| Action  | Default Gradle invocation                           |
|---------|-----------------------------------------------------|
| lint    | `spotlessCheck checkstyleMain checkstyleTest`       |
| format  | `spotlessApply`                                     |
| test    | `test`, plus `--tests PATTERN` per selection item   |
| build   | `build`                                             |
| check   | `build` (one call; Gradle's build runs the checks)  |
| clean   | `clean`                                             |

- Constructor keyword arguments override each task list.
- `release_assets`: `build/libs/*.jar` and `*/build/libs/*.jar`.
- `release_task: str | None = None`: when set, `devops release` asks for the same typed confirmation, then runs
  `gradlew <release_task>` instead of `ReleasePipeline` (template.java uses `doFullRelease`).

### Declared Files
- src/support_python/devops/projects.py
- src/support_python/devops/__init__.py
- tests/test_devops_projects_gradle.py
- README.md
- CHANGELOG.md

### Tests
- Unit: each action runs the mapped Gradle tasks through the stubbed runner; overrides replace them.
- Unit: the wrapper path is `gradlew.bat` on Windows and `gradlew` elsewhere.
- Unit: `release_task` delegation runs the task after confirmation; assets glob the jar locations.
- Integration: in a temporary directory with a fake wrapper script that records its arguments,
  `DevopsCli(GradleProject(tmp)).run(["check"])` exits 0 and records `build`.
- Integration: `DevopsCli(GradleProject(Path("../template.java"))).run(["versions"])` exits 0 (read-only).

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration checks above.
Size estimate: 5 files, 300 lines.
