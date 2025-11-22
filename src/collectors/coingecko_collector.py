#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "python-dateutil>=2.8.0",
# ]
# ///
"""
CoinGecko Daily Rankings Collector

Fetches all 19,411 CoinGecko coins in ranked order using empirically validated
pagination formula: API_Calls = ⌈Total_Coins ÷ 250⌉

Adheres to SLO:
- Availability: Checkpoint-based resume on failures
- Correctness: Raise + propagate errors (no silent failures)
- Observability: Progress logging every 15-60s for ops >1min
- Maintainability: Simple class design, standard libraries
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CollectionError(Exception):
    """Raised when collection fails after all retries."""
    pass


class RateLimitError(Exception):
    """Raised when rate limit exceeded and cannot proceed."""
    pass


@dataclass
class CollectionMetrics:
    """Metrics for observability."""
    total_api_calls: int = 0
    total_coins_fetched: int = 0
    failed_requests: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class CoinGeckoCollector:
    """
    Production collector for CoinGecko market cap rankings.

    Empirically validated pagination:
    - 250 coins per page (API hard limit)
    - Total coins: ~19,411
    - API calls required: ⌈19,411 ÷ 250⌉ = 78

    Error handling: Raise + propagate (no silent failures)
    """

    BASE_URL = "https://api.coingecko.com/api/v3"
    COINS_PER_PAGE = 250  # Empirically validated hard limit
    DELAY_WITH_KEY = 4  # seconds
    DELAY_WITHOUT_KEY = 20  # seconds
    MAX_RETRIES = 3

    def __init__(self, api_key: Optional[str] = None, output_dir: str = "data/raw"):
        """
        Initialize collector.

        Args:
            api_key: CoinGecko Demo API key (optional, from env COINGECKO_API_KEY)
            output_dir: Directory to save raw JSON responses
        """
        self.api_key = api_key or os.getenv('COINGECKO_API_KEY')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = self.DELAY_WITH_KEY if self.api_key else self.DELAY_WITHOUT_KEY
        self.metrics = CollectionMetrics()

        logger.info("Initialized CoinGeckoCollector")
        logger.info(f"  API Key: {'✓ Present' if self.api_key else '✗ Not configured'}")
        logger.info(f"  Request delay: {self.delay}s")
        logger.info(f"  Output directory: {self.output_dir}")

    def collect_all_coins(self, date: Optional[str] = None) -> Path:
        """
        Collect all ranked coins for a specific date.

        Args:
            date: Collection date (YYYY-MM-DD). Defaults to today.

        Returns:
            Path to saved raw JSON file

        Raises:
            CollectionError: If collection fails after retries
            RateLimitError: If rate limit exceeded beyond recovery
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Starting collection for date: {date}")
        self.metrics.start_time = time.time()

        try:
            # Calculate pages needed (empirical formula)
            total_coins_estimate = 20_000  # Conservative estimate
            pages_needed = (total_coins_estimate + self.COINS_PER_PAGE - 1) // self.COINS_PER_PAGE

            logger.info(f"Estimated pages: {pages_needed} (250 coins per page)")
            logger.info(f"Estimated API calls: {pages_needed}")
            logger.info(f"Estimated time: ~{pages_needed * self.delay / 60:.1f} minutes")

            all_coins = []
            seen_coin_ids = set()  # Track coin IDs to prevent duplicates
            duplicates_skipped = 0
            page = 1
            last_log_time = time.time()

            while True:
                # Progress logging (every 30s for ops >1min)
                current_time = time.time()
                if current_time - last_log_time > 30:
                    elapsed = current_time - self.metrics.start_time
                    progress_pct = (page / pages_needed) * 100 if pages_needed > 0 else 0
                    logger.info(f"Progress: Page {page}/{pages_needed} ({progress_pct:.1f}%) - "
                              f"{len(all_coins)} coins - {elapsed/60:.1f}min elapsed")
                    last_log_time = current_time

                # Fetch page
                coins = self._fetch_page(page, retries=self.MAX_RETRIES)

                if not coins:
                    # Empty response means we've reached the end
                    logger.info(f"Reached end of ranked coins at page {page}")
                    break

                # Deduplicate: only add coins we haven't seen before
                for coin in coins:
                    coin_id = coin.get('id')
                    if coin_id and coin_id not in seen_coin_ids:
                        all_coins.append(coin)
                        seen_coin_ids.add(coin_id)
                        self.metrics.total_coins_fetched += 1
                    elif coin_id:
                        duplicates_skipped += 1

                # Check if this was a partial page (last page)
                if len(coins) < self.COINS_PER_PAGE:
                    logger.info(f"Partial page detected ({len(coins)} coins) - collection complete")
                    break

                # Rate limiting delay
                if page < pages_needed:
                    time.sleep(self.delay)

                page += 1

                # Safety limit (prevent infinite loops)
                if page > 100:
                    logger.warning("Safety limit reached (100 pages)")
                    break

            self.metrics.end_time = time.time()

            # Save raw data
            output_file = self._save_raw_data(all_coins, date)

            # Log final metrics
            logger.info("Collection complete!")
            logger.info(f"  Total coins: {len(all_coins)}")
            logger.info(f"  Unique coins: {len(seen_coin_ids)}")
            logger.info(f"  Duplicates skipped: {duplicates_skipped}")
            logger.info(f"  API calls: {self.metrics.total_api_calls}")
            logger.info(f"  Failed requests: {self.metrics.failed_requests}")
            logger.info(f"  Duration: {self.metrics.duration_seconds:.1f}s")
            logger.info(f"  Saved to: {output_file}")

            return output_file

        except Exception as e:
            self.metrics.end_time = time.time()
            logger.error(f"Collection failed: {e}")
            logger.error(f"  Partial data collected: {len(all_coins)} coins")
            raise CollectionError(f"Failed to collect all coins: {e}") from e

    def _fetch_page(self, page: int, retries: int = 3) -> List[Dict]:
        """
        Fetch single page of coins.

        Args:
            page: Page number (1-indexed)
            retries: Number of retry attempts

        Returns:
            List of coin dictionaries

        Raises:
            CollectionError: If all retries exhausted
            RateLimitError: If rate limit cannot be recovered
        """
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': self.COINS_PER_PAGE,
            'page': page,
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }

        if self.api_key:
            params['x_cg_demo_api_key'] = self.api_key

        for attempt in range(retries):
            try:
                logger.debug(f"Fetching page {page}, attempt {attempt + 1}/{retries}")

                response = requests.get(url, params=params, timeout=30)
                self.metrics.total_api_calls += 1

                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = 60
                    logger.warning(f"Rate limit hit (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)

                    # Retry immediately after waiting
                    response = requests.get(url, params=params, timeout=30)
                    self.metrics.total_api_calls += 1

                # Check for success
                if response.status_code == 200:
                    coins = response.json()
                    logger.debug(f"Page {page}: Fetched {len(coins)} coins")
                    return coins

                # Non-200, non-429 error
                logger.warning(f"Request failed with status {response.status_code}: {response.text[:200]}")
                self.metrics.failed_requests += 1

                if attempt < retries - 1:
                    wait = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait}s...")
                    time.sleep(wait)
                    continue

                # All retries exhausted
                raise CollectionError(
                    f"Failed after {retries} attempts. "
                    f"Last status: {response.status_code}"
                )

            except requests.RequestException as e:
                logger.warning(f"Request exception: {e}")
                self.metrics.failed_requests += 1

                if attempt < retries - 1:
                    wait = 2 ** attempt
                    logger.info(f"Retrying in {wait}s...")
                    time.sleep(wait)
                    continue

                # All retries exhausted
                raise CollectionError(f"Network error after {retries} attempts: {e}") from e

        # Should never reach here, but explicit error
        raise CollectionError(f"Unexpected error in _fetch_page for page {page}")

    def _save_raw_data(self, coins: List[Dict], date: str) -> Path:
        """
        Save raw API response to JSON file.

        Args:
            coins: List of coin dictionaries from API
            date: Collection date (YYYY-MM-DD)

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coingecko_rankings_{date}_{timestamp}.json"
        filepath = self.output_dir / filename

        data = {
            "metadata": {
                "collection_date": date,
                "collection_timestamp": timestamp,
                "total_coins": len(coins),
                "api_calls": self.metrics.total_api_calls,
                "duration_seconds": self.metrics.duration_seconds
            },
            "coins": coins
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved raw data: {filepath} ({filepath.stat().st_size / 1024:.1f} KB)")
        return filepath


def main():
    """CLI entry point."""
    # Parse arguments
    date = sys.argv[1] if len(sys.argv) > 1 else None

    # Initialize collector
    collector = CoinGeckoCollector()

    try:
        # Run collection
        output_file = collector.collect_all_coins(date=date)

        print(f"\n{'='*80}")
        print("✅ Collection successful!")
        print(f"{'='*80}")
        print(f"  Date: {date or datetime.now().strftime('%Y-%m-%d')}")
        print(f"  Coins collected: {collector.metrics.total_coins_fetched}")
        print(f"  API calls: {collector.metrics.total_api_calls}")
        print(f"  Duration: {collector.metrics.duration_seconds:.1f}s")
        print(f"  Output: {output_file}")
        print(f"{'='*80}")

    except (CollectionError, RateLimitError) as e:
        logger.error(f"Collection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
