# Processes

Cross-platform process listing and ancestor-protected termination, implemented in [processes.py](../../src/support_python/tools/processes.py) and exposed on the command line as `processes`.
Specifications: [JSON output](../specs/json-output.md).

---

## Command-Line Interface
Run actions through the `processes` console script, built on the helpers in [processes.py](../../src/support_python/processes.py):
```bash
processes kill PID... [--force] [--dry-run] [--yes] [--format text|json]
processes list [--cwd PATH] [--open-path PATH] [--started-before TIMESTAMP] [--started-after TIMESTAMP] [--ancestors-of PID] [--descendants-of PID] [--format text|json]
```

- `kill` is the default action, so `processes 1234` runs `processes kill 1234`.
- `kill` terminates each PID in turn and skips the current process and its ancestors with a `WARN` message.
- `kill` asks for a typed confirmation (`kill`) before terminating anything; a wrong answer or end of input exits `1`.
- `--yes` skips the confirmation. Without `--yes` and without a terminal on `stdin`, `kill` terminates nothing and exits `2`.
- `--force` terminates with `SIGKILL` on POSIX or `taskkill /F` on Windows.
- `--dry-run` prints `Would kill PID {{pid}}` or `Would skip protected PID {{pid}}` per PID, terminates nothing, never asks for confirmation, and exits `0`.
- `kill --format json` prints one JSON array on `stdout` with an object `{"pid", "outcome"}` per PID, and log messages, the confirmation summary, and the confirmation prompt go to `stderr`.
- The `outcome` is `killed`, `skipped-protected`, `not-found`, or `failed` (with a `detail` message); `--dry-run` reports `would-kill` or `would-skip-protected`.
- The array is empty when the protected process hierarchy cannot be inspected. Exit codes match `--format text`.
- `list` prints running processes that match every given filter.
- `--cwd PATH` keeps processes whose working directory is `PATH` or below it.
- `--open-path PATH` keeps processes holding `PATH` open.
- `--started-before` and `--started-after` take ISO-8601 dates or datetimes as start-time bounds.
- `--ancestors-of PID` and `--descendants-of PID` keep the process tree above or below `PID`, `PID` included.
- `--format text|json` selects the human-readable table or a single JSON array on `stdout` (default: `text`).
- In `json` mode, log messages go to `stderr` so `stdout` holds only the JSON document.
- The former `--format table` value is rejected with exit code `2`; use `--format text` instead.

Exit codes:
- `0` on success, including protected PIDs that were skipped.
- `1` on operational failure while inspecting or terminating processes.
- `2` on invalid arguments.

---

## Examples
```bash
processes kill 1234 5678 --dry-run
processes kill 1234 --force --yes
processes list --cwd /path/to/workdir
processes list --open-path /path/to/file.txt --format json
processes list --open-path locked.txt --started-after 2026-11-07T00:00:00
processes list --descendants-of 1234
```
