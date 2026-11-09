## Walkthrough & Validation

### Full Test Suite
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m pytest -q`
Exit code: `0`
```text
........................................................................ [ 10%]
................................................................s....... [ 20%]
........................................................................ [ 30%]
...s......s............................................................. [ 40%]
........................................................................ [ 51%]
........................................................................ [ 61%]
......................................................................................................................................................................................... [ 87%]
........................................... [ 93%]
............................................                         [100%]
701 passed, 3 skipped, 64 subtests passed in 165.60s (0:02:45)
```

### Installed CLI Integration Check
Command: `C:\Dev-Projects\support.python\.venv\Scripts\git-repository-backup.exe list --format json` (with `HOME` and `USERPROFILE` pointing at a temporary directory holding only `~/.config/backup-git-repos/config.json`)
Exit code: `0`
```text
EXIT: 0
STDOUT:
[
  {
    "name": "alpha",
    "path": "C:\\Users\\giova\\AppData\\Local\\Temp\\t0027-vw29ioh1\\root\\alpha"
  }
]
STDERR:
**[WARN]**  Reading legacy config C:\Users\giova\AppData\Local\Temp\t0027-vw29ioh1\home\.config\backup-git-repos\config.json; move it to C:\Users\giova\AppData\Local\Temp\t0027-vw29ioh1\home\.config\git-repository-backup\config.json. The legacy path is dropped in v3.0.0.
```

### Linting and Formatting
Command: `C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m ruff check . && C:\Dev-Projects\support.python\.venv\Scripts\python.exe -m ruff format --check .`
Exit code: `0`
```text
All checks passed!
97 files already formatted
```
