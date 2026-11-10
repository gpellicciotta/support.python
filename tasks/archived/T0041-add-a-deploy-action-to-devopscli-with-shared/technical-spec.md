### API
```python
@dataclass(frozen=True)
class DeployStep:
    name: str
    command: Sequence[str] | None = None
    action: Callable[["DeployContext"], bool] | None = None   # exactly one of command and action

@dataclass
class DeployContext:
    project: Project
    version: str
    logger: CliLogger
    dry_run: bool

DevopsCli.set_deploy(
    steps: Sequence[DeployStep],
    verify: Callable[[DeployContext], bool] | None = None,
    require_ci: bool = True,
    environment: str = "production",
) -> None
```

### Command-Line Interface
```text
devops deploy [--dry-run] [--yes] [--skip-ci-check]
```
- Without `set_deploy`, `deploy` is neither listed nor accepted.
- CI check: `gh run list --commit <HEAD sha> --json status,conclusion --limit 20`; it passes when a completed run succeeded
  and none failed. A missing `gh` fails with a hint about `--skip-ci-check`.
- Confirmation reuses `confirm_typed` from T0036.
- Command steps run through the injectable runner; exit codes follow ADR-0003.

### Declared Files
- src/support_python/devops/deploy.py
- src/support_python/devops/cli.py
- src/support_python/devops/__init__.py
- tests/test_devops_deploy.py
- README.md
- CHANGELOG.md

### Tests
- Unit: each failing precondition exits 1 before any step runs.
- Unit: a dry run runs no step; a declined confirmation exits 1; a failing step stops the rest.
- Unit: a failing verification exits 1; without `set_deploy` the action is absent.
- Integration: in a temporary repository with a local bare `origin`, a pushed `v1.0.0` tag, and a runner stubbing only `gh`,
  `run(["deploy", "--yes"])` runs two command steps that write marker files, then the verification callback, in order.

Completion check: `.venv/Scripts/python -m pytest -q`, including the integration scenario above.
Size estimate: 6 files, 400 lines.
