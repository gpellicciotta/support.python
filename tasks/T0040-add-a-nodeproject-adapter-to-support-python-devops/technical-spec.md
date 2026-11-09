### Script Mapping
| Action  | Command                                                                  |
|---------|--------------------------------------------------------------------------|
| lint    | `npm run lint`                                                           |
| format  | `npm run format`                                                         |
| test    | `npm test`, passing selection items after `--`                           |
| build   | `npm run build` when defined, then `npm pack --pack-destination dist`    |
| check   | lint, test, then build                                                   |
| clean   | remove `dist/`                                                           |

- A missing npm script logs an error naming the script and `package.json`, then fails with exit 1.
- `release_assets`: `dist/*.tgz`.

### Declared Files
- src/support_python/devops/projects.py
- src/support_python/devops/__init__.py
- tests/test_devops_projects_node.py
- README.md
- CHANGELOG.md

### Tests
- Unit: each action runs the mapped npm commands through the stubbed runner.
- Unit: a missing script fails with a clear message; build without a `build` script only packs.
- Integration: in a temporary directory whose `package.json` defines `lint` and `test` as `node -e "process.exit(0)"`,
  `DevopsCli(NodeProject(tmp)).run(["check"])` exits 0 and leaves a tarball in `dist/`; waive if Node.js is absent.
- Integration: `DevopsCli(NodeProject(Path("../support.js"))).run(["versions"])` exits 0 (read-only).

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration checks above.
Size estimate: 5 files, 300 lines.
