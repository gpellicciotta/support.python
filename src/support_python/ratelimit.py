"""Sliding-window task rate limiting utilities.

Provides :class:`TaskRateLimiter` to cap task dispatches across a configurable
sliding time window while supporting injected timestamps for deterministic testing.
"""

from __future__ import annotations

import time


class TaskRateLimiter:
    """Sliding-window rate limiter to cap the number of task dispatches per window.

    Attributes:
        max_tasks_per_hour: Maximum allowed dispatches in the sliding window, or None for unlimited.
        window_seconds: Duration of the sliding window in seconds (default: 3600.0).
        dispatch_timestamps: List of epoch timestamps of recorded dispatches in the current window.
    """

    def __init__(self, max_tasks_per_hour: int | None = None, window_seconds: float = 3600.0) -> None:
        """Initialize a TaskRateLimiter instance.

        Args:
            max_tasks_per_hour: Integer dispatch cap per window, or None.
            window_seconds: Window duration in seconds (default: 3600.0).
        """
        self.max_tasks_per_hour = max_tasks_per_hour
        self.window_seconds = window_seconds
        self.dispatch_timestamps: list[float] = []

    @property
    def is_enabled(self) -> bool:
        """Check whether rate limiting is actively enabled.

        Returns:
            True if max_tasks_per_hour is configured and greater than zero; False otherwise.
        """
        return self.max_tasks_per_hour is not None and self.max_tasks_per_hour > 0

    def prune(self, now: float | None = None) -> None:
        """Remove recorded dispatch timestamps outside the sliding window.

        Args:
            now: Current reference epoch timestamp, or None to use ``time.time()``.
        """
        if not self.is_enabled:
            return
        current_time = now if now is not None else time.time()
        cutoff = current_time - self.window_seconds
        self.dispatch_timestamps = [ts for ts in self.dispatch_timestamps if ts > cutoff]

    def can_dispatch(self, now: float | None = None) -> bool:
        """Check whether a new task dispatch is permitted under the cap.

        Args:
            now: Current reference epoch timestamp, or None to use ``time.time()``.

        Returns:
            True if dispatch is allowed; False if the rate limit is reached.
        """
        if not self.is_enabled:
            return True
        self.prune(now)
        assert self.max_tasks_per_hour is not None
        return len(self.dispatch_timestamps) < self.max_tasks_per_hour

    def get_wait_duration(self, now: float | None = None) -> float:
        """Calculate wait seconds until the next dispatch slot becomes available.

        Args:
            now: Current reference epoch timestamp, or None to use ``time.time()``.

        Returns:
            Wait duration in seconds (0.0 if dispatch is currently allowed, or at least 1.0 when blocked).
        """
        if not self.is_enabled:
            return 0.0
        self.prune(now)
        assert self.max_tasks_per_hour is not None
        if len(self.dispatch_timestamps) < self.max_tasks_per_hour:
            return 0.0
        current_time = now if now is not None else time.time()
        oldest_ts = self.dispatch_timestamps[0]
        wait_seconds = (oldest_ts + self.window_seconds) - current_time
        return max(1.0, wait_seconds)

    def record_dispatch(self, now: float | None = None) -> None:
        """Record a task dispatch timestamp in the sliding window.

        Args:
            now: Dispatch epoch timestamp, or None to use ``time.time()``.
        """
        if not self.is_enabled:
            return
        current_time = now if now is not None else time.time()
        self.dispatch_timestamps.append(current_time)


__all__ = [
    "TaskRateLimiter",
]
