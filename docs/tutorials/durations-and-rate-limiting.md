# Durations and Rate Limiting

These modules parse and format durations and timestamps, and limit how often tasks dispatch:
- [durations.py](../../src/support_python/durations.py): duration and timestamp parsing and human-readable formatting.
  It uses only the standard library and leaves `support_python.dates.format_datetime` unchanged.
- [ratelimit.py](../../src/support_python/ratelimit.py): the sliding-window `TaskRateLimiter`, using only the standard library.

Their symbols are re-exported from `support_python` and also available through `support_python.durations` and `support_python.ratelimit`.

## Durations and timestamps
```python
from support_python import (
    format_duration,
    format_epoch,
    format_past_epoch,
    format_short_duration,
    parse_date_or_datetime,
    parse_duration_to_seconds,
    parse_iso8601,
)

seconds = parse_duration_to_seconds("1h 02m 05s")  # 3725.0
label = format_duration(seconds)  # "1h 02m 05s"
short = format_short_duration(seconds)  # "1h 2m"
ts = parse_iso8601("2026-09-11T10:00:00Z")
dt = parse_date_or_datetime("2026-09-11 10:00:00")
future = format_epoch(ts + seconds, now_ts=ts)
past = format_past_epoch(ts, now_ts=ts + seconds)
```

- `parse_iso8601(text)` parses an ISO 8601 timestamp (including trailing `Z`) into a POSIX float timestamp, or `None` on invalid input.
- `parse_date_or_datetime(text)` parses `YYYY-MM-DD`, `YYYY-MM-DD[T ]HH:MM[:SS]`, or a `YYYY-MM-DD` prefix into a naive `datetime`, or `None`.
- `parse_duration_to_seconds(dur_str, default_unit="s")` parses single or compound units (`d`, `h`, `m`, `s`, `ms`) and bare numbers into seconds.
  It returns `None` for invalid or negative input.
- `format_duration(seconds)` formats durations as `{{s.f}}s`, `{{m}}m {{ss}}s`, `{{h}}h {{mm}}m {{ss}}s`, or `{{d}}d {{hh}}h` (clamping negatives to `0.0s`).
- `format_short_duration(seconds)` formats durations as `{{s}}s` under 2 minutes, `{{m}}m` under 1 hour, `{{h}}h {{m}}m` under 1 day, or `{{d}}d {{h}}h`.
- `format_epoch(ts, now_ts=None)` formats a target timestamp as `YYYY-MM-DD HH:MM:SS (in {{duration}})`.
- `format_past_epoch(ts, now_ts=None)` formats a past timestamp as `YYYY-MM-DD HH:MM ({{short-duration}} ago)`.

## Task rate limiter
`TaskRateLimiter` pairs with the duration helpers for wait-duration formatting:

```python
from support_python import TaskRateLimiter, format_duration

limiter = TaskRateLimiter(max_tasks_per_hour=2, window_seconds=3600.0)
if limiter.can_dispatch():
    limiter.record_dispatch()
else:
    wait_seconds = limiter.get_wait_duration()
    print(f"Rate limit reached; retry in {format_duration(wait_seconds)}")
```

- `TaskRateLimiter(max_tasks_per_hour=None, window_seconds=3600.0)` tracks dispatch timestamps in a sliding window.
- `is_enabled` is `True` only when `max_tasks_per_hour` is set and greater than `0`.
- `prune(now=None)` removes recorded timestamps at or before `now - window_seconds`.
- `can_dispatch(now=None)` prunes expired timestamps and returns `True` when disabled or below capacity.
- `get_wait_duration(now=None)` returns `0.0` when dispatch is allowed, or `max(1.0, oldest + window_seconds - now)` when blocked.
- `record_dispatch(now=None)` appends a dispatch timestamp when enabled.
