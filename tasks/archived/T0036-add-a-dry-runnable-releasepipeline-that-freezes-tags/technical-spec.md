### API
```python
def confirm_typed(summary: Sequence[str], phrase: str, *, input_fn: Callable[[str], str] = input) -> bool

@dataclass
class ReleasePipeline:
    root: Path
    logger: CliLogger
    quality_check: Callable[[], bool] | None = None      # None skips quality checks
    assets: Callable[[], Sequence[Path]] | None = None   # resolved after the quality check
    main_branch: str = "main"
    dry_run: bool = False
    assume_yes: bool = False
    runner: Callable[[Sequence[str]], int] = run_step_command   # adapt the signature as needed
    input_fn: Callable[[str], str] = input
    today: Callable[[], date] = date.today

    def run(self) -> int   # 0 released or dry run complete, 1 precondition, confirmation, or step failure
```

### Flow
1. Read the version; derive the release version, the next `-pre` version, and whether a freeze is needed.
2. Preconditions, all before any change:
   - clean working tree, allowing only the version file and `CHANGELOG.md` when a freeze is needed;
   - current branch is `main_branch`;
   - `gh` is installed and authenticated;
   - `git fetch origin <main_branch> --tags` succeeds;
   - tag `v<X>` is absent on origin, and no GitHub release `v<X>` exists;
   - release notes for `<X>` are non-empty.
3. Run `quality_check` when given; failure exits 1.
4. Print the planned commands, then require typing `release v<X>` unless `assume_yes`; declining exits 1 with nothing changed.
5. Freeze when needed: `freeze_changelog(..., f"released: {today}")`, set the version file, commit `Released version <X>.`.
6. Tag `v<X>`, push `main_branch` and the tag.
7. Run `gh release create v<X> --title v<X> --notes-file <temp file> [assets...]`.
8. Reopen: `open_dev_changelog`, set the version file to the next `-pre`, commit
   `Started version <next> after the <X> release.`, and push `main_branch`.
- With `dry_run`, every step logs what it would do and nothing runs or changes.

### Declared Files
- src/support_python/devops/release.py
- src/support_python/devops/__init__.py
- tests/test_devops_release_pipeline.py
- README.md
- CHANGELOG.md

### Tests
- Unit: each precondition failure exits 1 before any write, commit, or command with side effects.
- Unit: a dry run performs no writes, commits, tags, or pushes, and logs every planned command.
- Unit: a declined confirmation exits 1 with the repository unchanged.
- Unit: an already-frozen version skips the freeze commit.
- Integration: in a temporary repository with a local bare `origin` and a runner stubbing only `gh`,
  `run()` with `assume_yes` creates the freeze commit, pushes tag `v1.0.0`, calls `gh release create` with notes and assets,
  and pushes a `1.0.1-pre` reopening commit.

Completion check: `.venv/Scripts/python -m pytest -q`, including the integration scenario above.
Size estimate: 5 files, 450 lines.
Size note: the pipeline steps form one transaction; a partial pipeline could not release anything.
