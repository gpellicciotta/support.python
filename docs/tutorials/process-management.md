# Process Management

[processes.py](../../src/support_python/processes.py) inspects process hierarchies and terminates processes safely.
All helpers use only the Python standard library and `ctypes`.
The `processes` command-line tool in [tools/processes.py](../../src/support_python/tools/processes.py) builds on them; see [processes.md](../tools/processes.md) for its actions and examples.

## Example

```python
import os
from support_python.processes import (
    get_process_cwd,
    get_process_descendants,
    get_process_hierarchy,
    get_process_start_time,
    is_process_alive,
    list_processes,
    safe_kill,
    terminate_process_tree,
)

pid = os.getpid()
ancestors = get_process_hierarchy(pid)
descendants = get_process_descendants(pid)
cwd = get_process_cwd(pid)
started = get_process_start_time(pid)
alive = is_process_alive(pid, expected_start=started, slack_seconds=2.0)
matching = list_processes(cwd=cwd, descendants_of=pid)
safe_kill([pid])  # Skips the current process and its ancestors with a warning.
```

## Helpers
- `get_process_hierarchy(start_pid)` returns `start_pid` and all ancestor PIDs, failing closed with `OSError` when inspection fails.
- `get_process_descendants(start_pid)` returns `start_pid` and all child and descendant PIDs.
- `get_process_cwd(pid)` and `find_pids_with_open_path(path)` inspect process working directories and open files across Windows, Linux, and macOS.
- `list_processes(...)` and `filter_processes(...)` filter `ProcessInfo` records by working directory, open path, start time, ancestors, and descendants.
  These filters back the `processes list` options `--cwd`, `--open-path`, `--started-before`, `--started-after`, `--ancestors-of`, and `--descendants-of`.
- `windows_parent_map()` enumerates running Windows processes via `CreateToolhelp32Snapshot` without spawning a shell.
- `get_process_start_time(pid)` returns a naive local `datetime`, or `None` if the process is absent.
- `is_process_alive(pid, expected_start=None, slack_seconds=2.0)` checks liveness and guards against recycled PIDs.
- `terminate_process(pid, force=False)` signals one positive PID directly; callers must enforce ancestor protection first.
- `terminate_process_tree(pid)` terminates a process and its child tree, returning `False` on invalid PIDs or failures.
- `safe_kill(pids, logger=None, force=False)` skips the current process and ancestors with a warning and returns `bool`.
