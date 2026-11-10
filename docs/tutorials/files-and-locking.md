# Files and Locking

These modules keep shared files consistent across concurrent readers, writers, and processes:
- [files.py](../../src/support_python/files.py): atomic UTF-8 text writes and retry-hardened replaces and reads, using only the standard library.
- [locking.py](../../src/support_python/locking.py): file, null, Redis, and MySQL locks behind one factory; the core has no Python dependencies.

Their symbols are re-exported from `support_python` and also available through `support_python.files` and `support_python.locking`.

## Atomic text files
```python
from pathlib import Path
from support_python import atomic_replace, atomic_write_text, read_text_retrying

path = Path("state.txt")
atomic_write_text(path, "consistent text\n")
content = read_text_retrying(path, errors="strict")
```

- `atomic_write_text(path, content, newline=None)` writes UTF-8 text via a temporary sibling file so readers never see partial content.
- `atomic_write_text` preserves existing POSIX permission bits, omits the target filename from the temporary name, and removes failed temporaries.
- `atomic_replace(src, dst, max_retries=15, base_delay=0.01)` replaces `dst` with `src`, retrying transient `PermissionError` and Windows error `5` or `32`.
- `read_text_retrying(path, max_retries=10, base_delay=0.005, errors="replace")` reads UTF-8 text while retrying transient `PermissionError` locks during concurrent renames.

## Locks
```python
from support_python import LockTimeoutError, create_lock

lock = create_lock("file", path=".app/.app.lock", timeout=5.0)
try:
    with lock:
        ...  # Critical section; nested `with` blocks in one thread are re-entrant.
except LockTimeoutError as error:
    print(error)  # Includes holder diagnostics when the holder is in this process.
```

- `FileLock` uses `msvcrt` on Windows and `fcntl` elsewhere; the OS frees it when a process dies.
- `NullLock` always succeeds; use it for tests or disabled locking.
- `RedisLock` provides distributed locking backed by Redis using `SET NX PX` and an atomic Lua release script.
  It requires the `redis` optional extra (`pip install support-python[redis]`).
- `MySQLLock` provides distributed server-wide advisory locking backed by MySQL using `GET_LOCK` and `RELEASE_LOCK`.
  It requires the `mysql` optional extra (`pip install support-python[mysql]`).
- `create_lock(backend, key, path, timeout, poll_interval, max_jitter, ttl)` maps `null`/`none` to `NullLock`.
  - `file`, `local`, or an empty value select `FileLock` and require `path`.
  - `redis://` and `rediss://` select `RedisLock` and require `key`.
  - `mysql://`, `mysql+pymysql://`, and `jdbc:mysql://` select `MySQLLock` and require `key`.
  - Unsupported schemes raise `ValueError`.
- Timeouts and TTLs are floats in seconds.
