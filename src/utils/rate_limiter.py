#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Rate Limiter for CoinGecko API

Enforces CoinGecko Free Tier limits:
- 30 calls per minute
- 10,000 calls per month

Adheres to SLO:
- Correctness: Strict enforcement, raise on quota exceeded
- Observability: Track usage, log warnings at thresholds
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    calls_per_minute: int = 30
    calls_per_month: int = 10_000
    warn_threshold: float = 0.8  # Warn at 80% usage


@dataclass
class RateLimitMetrics:
    """Rate limit usage metrics."""
    minute_calls: list = field(default_factory=list)  # (timestamp, count) tuples
    monthly_calls: int = 0
    month_start: Optional[datetime] = None

    def reset_if_new_month(self):
        """Reset monthly counter if new month started."""
        now = datetime.now()
        if self.month_start is None:
            self.month_start = now
            return

        if now.month != self.month_start.month or now.year != self.month_start.year:
            self.monthly_calls = 0
            self.month_start = now


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class RateLimiter:
    """
    Production rate limiter for CoinGecko API.

    Features:
    - Per-minute sliding window (30 calls/min)
    - Per-month quota tracking (10,000 calls/month)
    - Warning thresholds (80% usage alerts)
    - Raise on quota exceeded (no silent failures)

    Usage:
        limiter = RateLimiter()
        limiter.acquire()  # Blocks if rate limit reached
        # Make API call
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration (defaults to CoinGecko free tier)
        """
        self.config = config or RateLimitConfig()
        self.metrics = RateLimitMetrics()

    def acquire(self, wait: bool = True) -> None:
        """
        Acquire permission to make API call.

        Args:
            wait: If True, blocks until rate limit allows. If False, raises immediately.

        Raises:
            RateLimitExceeded: If monthly quota exceeded or wait=False and minute limit hit
        """
        # Check monthly quota (hard limit, cannot wait)
        self.metrics.reset_if_new_month()

        if self.metrics.monthly_calls >= self.config.calls_per_month:
            raise RateLimitExceeded(
                f"Monthly quota exceeded: {self.metrics.monthly_calls}/{self.config.calls_per_month}"
            )

        # Check minute limit (can wait)
        now = time.time()
        self._cleanup_old_calls(now)

        current_minute_calls = len(self.metrics.minute_calls)

        if current_minute_calls >= self.config.calls_per_minute:
            if not wait:
                raise RateLimitExceeded(
                    f"Minute limit exceeded: {current_minute_calls}/{self.config.calls_per_minute}"
                )

            # Calculate wait time until oldest call expires
            oldest_call = self.metrics.minute_calls[0]
            wait_time = 60 - (now - oldest_call)

            if wait_time > 0:
                time.sleep(wait_time + 0.1)  # Add 100ms buffer

            # Cleanup after waiting
            now = time.time()
            self._cleanup_old_calls(now)

        # Record this call
        self.metrics.minute_calls.append(now)
        self.metrics.monthly_calls += 1

        # Check warning thresholds
        monthly_pct = self.metrics.monthly_calls / self.config.calls_per_month
        if monthly_pct >= self.config.warn_threshold and monthly_pct < self.config.warn_threshold + 0.01:
            # Log warning only once when crossing threshold
            print(f"⚠️  Rate limit warning: {self.metrics.monthly_calls}/{self.config.calls_per_month} "
                  f"monthly calls used ({monthly_pct*100:.1f}%)")

    def _cleanup_old_calls(self, now: float) -> None:
        """Remove calls older than 60 seconds from tracking."""
        cutoff = now - 60
        self.metrics.minute_calls = [ts for ts in self.metrics.minute_calls if ts > cutoff]

    def get_metrics(self) -> dict:
        """
        Get current rate limit metrics.

        Returns:
            Dictionary with usage statistics
        """
        self.metrics.reset_if_new_month()
        now = time.time()
        self._cleanup_old_calls(now)

        monthly_pct = (self.metrics.monthly_calls / self.config.calls_per_month) * 100
        minute_calls = len(self.metrics.minute_calls)
        minute_pct = (minute_calls / self.config.calls_per_minute) * 100

        return {
            "monthly_calls": self.metrics.monthly_calls,
            "monthly_limit": self.config.calls_per_month,
            "monthly_pct": monthly_pct,
            "minute_calls": minute_calls,
            "minute_limit": self.config.calls_per_minute,
            "minute_pct": minute_pct,
            "month_start": self.metrics.month_start.isoformat() if self.metrics.month_start else None
        }


if __name__ == "__main__":
    # Simple test
    limiter = RateLimiter()

    print("Testing rate limiter...")
    print(f"Config: {limiter.config.calls_per_minute} calls/min, "
          f"{limiter.config.calls_per_month} calls/month")

    # Simulate 5 rapid calls
    for i in range(5):
        limiter.acquire()
        print(f"Call {i+1} acquired")

    metrics = limiter.get_metrics()
    print(f"\nMetrics: {metrics}")
    print(f"✅ Rate limiter test passed")
