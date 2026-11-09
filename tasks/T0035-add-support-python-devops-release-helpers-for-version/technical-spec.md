### API
```python
@dataclass(frozen=True)
class VersionFile:
    name: str                 # "pyproject.toml", "gradle.properties", or "package.json"
    pattern: re.Pattern[str]  # group 1 is the version
    template: str             # replacement, with "{version}"

VERSION_FILES: tuple[VersionFile, ...]   # checked in this order

def find_version_file(root: Path) -> Path | None
def read_version(root: Path) -> str                     # FileNotFoundError or ValueError when absent
def write_version(root: Path, version: str) -> None     # preserves line endings
def release_version(version: str) -> str                # "1.2.3-pre" -> "1.2.3"
def next_dev_version(version: str, part: str = "patch") -> str   # "1.2.3" -> "1.2.4-pre"; part: major|minor|patch
def changelog_top_version(text: str) -> str | None      # version of the first "## v" heading, suffix included
def extract_release_notes(text: str, version: str) -> str        # ValueError when missing or empty
def freeze_changelog(text: str, version: str, status: str) -> str  # "## vX-pre" -> "## vX [status]"
def open_dev_changelog(text: str, version: str) -> str  # inserts "## v<version>" after the first "---" line
def parse_github_repo(remote_url: str) -> str           # "owner/name" from https or ssh remotes
```
- `status` is a date (`2026-11-09`, frozen) or `released: 2026-11-09`, per this repository's CHANGELOG preamble.
- `freeze_changelog` leaves an already-frozen heading unchanged and raises `ValueError` when no heading matches.
- Write files atomically with `support_python.files`, preserving the original newline style.

### Sources to Consolidate
- `scripts/extract-release-notes.py`: `extract_release_notes`.
- `scripts/_repo_common.py`: `VERSION_FILES`, `read_changelog`, `write_changelog`, `current_version`, `set_version`.
- `scripts/install-from-github-release.py`: `parse_github_repo` (that script keeps its own copy, staying self-contained).
- `../template.python/scripts/devops.py`: `_next_dev_version`, `_finalize_changelog_heading`, `_prepend_dev_changelog_heading`.

### Declared Files
- src/support_python/devops/release.py
- src/support_python/devops/__init__.py
- tests/test_devops_release.py
- README.md
- CHANGELOG.md

### Tests
- Unit: version reading and writing for all three version files, including CRLF preservation.
- Unit: `next_dev_version` for each part; `release_version` with and without `-pre`.
- Unit: notes extraction for present, missing, and empty sections; freezing `-pre`, already-frozen, and missing headings.
- Unit: `open_dev_changelog` inserts after the separator; `parse_github_repo` handles https, ssh, and `.git` suffixes.
- Integration: in this repository, `read_version(Path("."))` equals `changelog_top_version` of `CHANGELOG.md`,
  and `extract_release_notes` for `1.3.5` equals `python scripts/extract-release-notes.py 1.3.5` output.

Completion check: `.venv/Scripts/python -m pytest -q`, plus the integration checks above.
Size estimate: 5 files, 400 lines.
