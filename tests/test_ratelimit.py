"""Unit and integration tests for support_python.ratelimit."""

from __future__ import annotations

import pytest

import support_python
from support_python import TaskRateLimiter, format_duration
import support_python.ratelimit as ratelimit


def test_disabled_when_none_or_non_positive() -> None:
    for cap in (None, 0, -1, -100):
        limiter = TaskRateLimiter(max_tasks_per_hour=cap)
        assert not limiter.is_enabled
        assert limiter.can_dispatch(now=100.0) is True
        assert limiter.get_wait_duration(now=100.0) == 0.0
        limiter.record_dispatch(now=100.0)
        assert limiter.dispatch_timestamps == []
        limiter.prune(now=200.0)
        assert limiter.dispatch_timestamps == []


def test_cap_of_two_blocks_third_and_allows_after_oldest_leaves_window() -> None:
    limiter = TaskRateLimiter(max_tasks_per_hour=2, window_seconds=3600.0)
    assert limiter.is_enabled

    assert limiter.can_dispatch(now=100.0) is True
    limiter.record_dispatch(now=100.0)

    assert limiter.can_dispatch(now=200.0) is True
    limiter.record_dispatch(now=200.0)

    assert limiter.can_dispatch(now=300.0) is False
    assert limiter.can_dispatch(now=3699.9) is False

    # At now=3700.0, cutoff is 100.0, so 100.0 (at cutoff) is dropped and dispatch is allowed.
    assert limiter.can_dispatch(now=3700.0) is True
    assert limiter.dispatch_timestamps == [200.0]


def test_prune_drops_timestamps_at_or_before_cutoff_and_keeps_newer() -> None:
    limiter = TaskRateLimiter(max_tasks_per_hour=5, window_seconds=1000.0)
    limiter.dispatch_timestamps = [50.0, 100.0, 100.001, 500.0]

    limiter.prune(now=1100.0)
    assert limiter.dispatch_timestamps == [100.001, 500.0]


def test_get_wait_duration_returns_remaining_with_one_second_minimum() -> None:
    limiter = TaskRateLimiter(max_tasks_per_hour=2, window_seconds=3600.0)
    limiter.record_dispatch(now=100.0)
    assert limiter.get_wait_duration(now=200.0) == 0.0

    limiter.record_dispatch(now=200.0)
    assert limiter.get_wait_duration(now=300.0) == pytest.approx(3400.0)
    assert limiter.get_wait_duration(now=3699.5) == pytest.approx(1.0)
    assert limiter.get_wait_duration(now=3699.999) == pytest.approx(1.0)
    assert limiter.get_wait_duration(now=3700.0) == 0.0


def test_custom_window_seconds_changes_window() -> None:
    limiter = TaskRateLimiter(max_tasks_per_hour=1, window_seconds=60.0)
    limiter.record_dispatch(now=10.0)

    assert limiter.can_dispatch(now=50.0) is False
    assert limiter.get_wait_duration(now=50.0) == pytest.approx(20.0)
    assert limiter.can_dispatch(now=69.5) is False
    assert limiter.get_wait_duration(now=69.5) == pytest.approx(1.0)
    assert limiter.can_dispatch(now=70.0) is True
    assert limiter.get_wait_duration(now=70.0) == 0.0


def test_integration_simulated_hour_lifecycle_and_export_surface() -> None:
    limiter = TaskRateLimiter(max_tasks_per_hour=3, window_seconds=3600.0)
    now = 1000.0

    # Dispatch 3 tasks at t=1000, t=1600, t=2200
    for offset in (0.0, 600.0, 1200.0):
        current = now + offset
        assert limiter.can_dispatch(now=current) is True
        assert limiter.get_wait_duration(now=current) == 0.0
        limiter.record_dispatch(now=current)

    # Blocked at t=2500 (oldest is 1000, expires at 4600 -> wait 2100s)
    now = 2500.0
    assert limiter.can_dispatch(now=now) is False
    wait = limiter.get_wait_duration(now=now)
    assert wait == pytest.approx(2100.0)
    assert format_duration(wait) == "35m 00s"

    # Advance near boundary t=4599.8 -> still blocked, wait clamped to 1.0s minimum
    now = 4599.8
    assert limiter.can_dispatch(now=now) is False
    wait_edge = limiter.get_wait_duration(now=now)
    assert wait_edge == pytest.approx(1.0)
    assert format_duration(wait_edge) == "1.0s"

    # Sleeping for wait_edge (1.0s) advances to t=4600.8 -> oldest (1000.0) pruned, slot reallowed
    now += wait_edge
    assert limiter.can_dispatch(now=now) is True
    assert limiter.get_wait_duration(now=now) == 0.0
    assert len(limiter.dispatch_timestamps) == 2

    # Record 4th dispatch at t=4600.8 -> full again until t=5200.0
    limiter.record_dispatch(now=now)
    assert limiter.can_dispatch(now=now) is False
    assert limiter.get_wait_duration(now=now) == pytest.approx(5200.0 - now)

    assert support_python.TaskRateLimiter is ratelimit.TaskRateLimiter
