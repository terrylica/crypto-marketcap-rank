#!/usr/bin/env python3
"""Unit tests for RateLimiter."""

import sys
import time
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.rate_limiter import RateLimitConfig, RateLimiter, RateLimitError


def test_rate_limiter_basic():
    """Test basic rate limiter functionality."""
    config = RateLimitConfig(calls_per_minute=5, calls_per_month=100)
    limiter = RateLimiter(config=config)

    # Should allow first 5 calls
    for i in range(5):
        limiter.acquire(wait=False)

    # 6th call should raise
    with pytest.raises(RateLimitError):
        limiter.acquire(wait=False)


def test_rate_limiter_metrics():
    """Test rate limiter metrics tracking."""
    config = RateLimitConfig(calls_per_minute=10, calls_per_month=100)
    limiter = RateLimiter(config=config)

    # Make 3 calls
    for i in range(3):
        limiter.acquire(wait=False)

    # Check metrics
    metrics = limiter.get_metrics()
    assert metrics["monthly_calls"] == 3
    assert metrics["minute_calls"] == 3
    assert metrics["monthly_limit"] == 100
    assert metrics["minute_limit"] == 10


def test_rate_limiter_monthly_quota():
    """Test monthly quota enforcement."""
    config = RateLimitConfig(calls_per_minute=100, calls_per_month=5)
    limiter = RateLimiter(config=config)

    # Exhaust monthly quota
    for i in range(5):
        limiter.acquire(wait=False)

    # Should raise on quota exceeded
    with pytest.raises(RateLimitError, match="Monthly quota exceeded"):
        limiter.acquire(wait=False)


def test_rate_limiter_cleanup():
    """Test that old calls are cleaned up."""
    config = RateLimitConfig(calls_per_minute=5, calls_per_month=100)
    limiter = RateLimiter(config=config)

    # Make 5 calls
    for i in range(5):
        limiter.acquire(wait=False)

    # Wait for cleanup (simulate 61 seconds passing)
    now = time.time()
    limiter.metrics.minute_calls = [now - 61, now - 61, now - 61, now - 61, now - 61]

    # Should allow new call after cleanup
    limiter.acquire(wait=False)

    metrics = limiter.get_metrics()
    assert metrics["minute_calls"] == 1  # Only the new call should remain


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
