#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pandas>=2.0.0",
#   "requests>=2.31.0",
# ]
# ///
"""
CoinGecko Free Tier Data Collection Script

ADR: 0001-hybrid-free-data-acquisition
Purpose: Collect 365-day historical market cap data for top 500 coins from CoinGecko free API

Usage:
    # Without API key (free, no registration):
    uv run tools/collect_coingecko.py --top-n 500 --output data/raw/coingecko

    # With Demo API key (recommended):
    export COINGECKO_API_KEY=your_key_here
    uv run tools/collect_coingecko.py --top-n 500 --output data/raw/coingecko --api-key $COINGECKO_API_KEY

    # Test mode (3 coins only):
    uv run tools/collect_coingecko.py --top-n 3 --output data/raw/coingecko --test

Exit Codes:
    0: Collection successful
    1: Collection failed (API error, rate limit, data quality issue)
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests


class CoinGeckoCollector:
    """Collects historical market cap data from CoinGecko free tier API."""

    BASE_URL = "https://api.coingecko.com/api/v3"
    RATE_LIMIT_DELAY = 4.0  # seconds between requests (15 calls/min - conservative for free tier)

    def __init__(self, api_key: Optional[str] = None, output_dir: str = "data/raw/coingecko", delay_override: Optional[float] = None):
        """
        Initialize collector.

        Args:
            api_key: Optional CoinGecko Demo API key
            output_dir: Output directory for collected data
            delay_override: Override default rate limit delay (for no-API-key usage)
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Override delay if specified
        if delay_override is not None:
            self.rate_limit_delay = delay_override
        else:
            self.rate_limit_delay = self.RATE_LIMIT_DELAY

        # Setup logging
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = Path("logs") / f"0001-coingecko-collection-{timestamp}.log"
        log_file.parent.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("CoinGecko Data Collection")
        self.logger.info(f"Log file: {log_file}")
        self.logger.info("")

        self.collected_data = []
        self.api_calls_made = 0
        self.start_time = None

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make API request with rate limiting and error handling.

        Args:
            endpoint: API endpoint (e.g., "/coins/list")
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            RuntimeError: If API request fails
        """
        url = f"{self.BASE_URL}{endpoint}"

        if params is None:
            params = {}

        # Add API key if provided
        if self.api_key:
            params['x_cg_demo_api_key'] = self.api_key

        # Rate limiting
        if self.api_calls_made > 0:
            time.sleep(self.rate_limit_delay)

        try:
            self.logger.debug(f"API Request: {url} with params: {params}")
            response = requests.get(url, params=params, timeout=30)
            self.api_calls_made += 1

            if response.status_code == 429:
                raise RuntimeError(
                    f"RATE LIMIT EXCEEDED (429)\n"
                    f"API calls made: {self.api_calls_made}\n"
                    f"CoinGecko free tier limit: 30 calls/minute\n"
                    f"RECOMMENDATION: Increase delay between requests or register for Demo API"
                )

            if response.status_code != 200:
                raise RuntimeError(
                    f"API request failed: {response.status_code}\n"
                    f"URL: {url}\n"
                    f"Response: {response.text[:500]}\n"
                    f"RECOMMENDATION: Check API status at https://status.coingecko.com/"
                )

            return response.json()

        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"API request timeout after 30 seconds\n"
                f"URL: {url}\n"
                f"RECOMMENDATION: Check network connection or try again later"
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(
                f"API request failed: {e}\n"
                f"URL: {url}\n"
                f"RECOMMENDATION: Check network connection"
            )

    def get_coin_list(self, top_n: int = 500) -> List[Dict]:
        """
        Get list of top N coins by market cap.

        Args:
            top_n: Number of top coins to retrieve

        Returns:
            List of coin dictionaries with id, symbol, name

        Raises:
            RuntimeError: If coin list retrieval fails
        """
        self.logger.info(f"Step 1: Retrieving top {top_n} coins...")

        # Get market data for top coins (current rankings)
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': min(top_n, 250),  # CoinGecko max per page
            'page': 1,
            'sparkline': 'false'
        }

        all_coins = []
        pages_needed = (top_n + 249) // 250  # Ceiling division

        for page in range(1, pages_needed + 1):
            params['page'] = page
            coins = self._make_request("/coins/markets", params)

            if not coins:
                raise RuntimeError(
                    f"No coins returned from /coins/markets (page {page})\n"
                    f"RECOMMENDATION: Check CoinGecko API status"
                )

            all_coins.extend(coins)
            self.logger.info(f"  Retrieved page {page}/{pages_needed}: {len(coins)} coins")

            if len(all_coins) >= top_n:
                break

        # Trim to exact top_n
        all_coins = all_coins[:top_n]

        self.logger.info(f"✅ Retrieved {len(all_coins)} coins")
        self.logger.info("  Sample coins:")
        for coin in all_coins[:5]:
            self.logger.info(f"    Rank {coin.get('market_cap_rank', 'N/A'):3d}: {coin['id']:20s} ({coin['symbol'].upper()})")
        self.logger.info("")

        return all_coins

    def collect_historical_data(self, coin_id: str, coin_symbol: str, coin_name: str, days: int = 365) -> List[Dict]:
        """
        Collect historical market chart data for a single coin.

        Args:
            coin_id: CoinGecko coin ID (e.g., "bitcoin")
            coin_symbol: Coin symbol (e.g., "BTC")
            coin_name: Coin name (e.g., "Bitcoin")
            days: Number of days of history (max 365 for free tier)

        Returns:
            List of records with date, symbol, name, price, market_cap, volume

        Raises:
            RuntimeError: If data collection fails
        """
        params = {
            'vs_currency': 'usd',
            'days': min(days, 365),  # Free tier max
            'interval': 'daily'
        }

        data = self._make_request(f"/coins/{coin_id}/market_chart", params)

        if 'prices' not in data or 'market_caps' not in data or 'total_volumes' not in data:
            raise RuntimeError(
                f"Incomplete data for {coin_id}\n"
                f"Expected: prices, market_caps, total_volumes\n"
                f"Received: {list(data.keys())}\n"
                f"RECOMMENDATION: Check API response format or skip this coin"
            )

        # Convert to records
        records = []
        prices = data['prices']
        market_caps = data['market_caps']
        volumes = data['total_volumes']

        # Ensure all arrays same length
        min_length = min(len(prices), len(market_caps), len(volumes))

        for i in range(min_length):
            timestamp_ms = prices[i][0]
            date = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')

            records.append({
                'date': date,
                'symbol': coin_symbol.upper(),
                'name': coin_name,
                'price': prices[i][1],
                'market_cap': market_caps[i][1],
                'volume_24h': volumes[i][1],
                'data_source': 'coingecko',
                'quality_tier': 'unverified'  # No circulating_supply to verify
            })

        return records

    def run_collection(self, top_n: int = 500, test_mode: bool = False) -> str:
        """
        Run full collection workflow.

        Args:
            top_n: Number of top coins to collect
            test_mode: If True, only collect 3 coins for testing

        Returns:
            Path to output CSV file

        Raises:
            RuntimeError: If collection fails
        """
        self.start_time = datetime.now()

        if test_mode:
            top_n = 3
            self.logger.info("⚠️  TEST MODE: Collecting only 3 coins")
            self.logger.info("")

        # Step 1: Get coin list
        coins = self.get_coin_list(top_n)

        # Step 2: Estimate collection time
        estimated_seconds = len(coins) * self.rate_limit_delay
        estimated_minutes = estimated_seconds / 60
        self.logger.info("Step 2: Estimation")
        self.logger.info(f"  Coins to collect: {len(coins)}")
        self.logger.info(f"  Rate limiting: {self.rate_limit_delay}s between requests")
        if self.api_key:
            self.logger.info("  API authentication: Demo API key (registered)")
        else:
            self.logger.info("  API authentication: None (no registration)")
        self.logger.info(f"  Estimated time: {estimated_minutes:.1f} minutes")
        self.logger.info("")

        # Step 3: Collect historical data
        self.logger.info("Step 3: Collecting historical data...")
        self.logger.info(f"  (This may take {estimated_minutes:.0f} minutes)")
        self.logger.info("")

        failed_coins = []

        for idx, coin in enumerate(coins, 1):
            coin_id = coin['id']
            coin_symbol = coin['symbol']
            coin_name = coin['name']

            try:
                self.logger.info(f"  [{idx}/{len(coins)}] Collecting {coin_id} ({coin_symbol.upper()})...")
                records = self.collect_historical_data(coin_id, coin_symbol, coin_name)
                self.collected_data.extend(records)
                self.logger.info(f"    ✅ {len(records)} records")

            except Exception as e:
                self.logger.error(f"    ❌ Failed: {e}")
                failed_coins.append({'id': coin_id, 'symbol': coin_symbol, 'error': str(e)})
                # Continue with next coin instead of stopping

        self.logger.info("")

        if not self.collected_data:
            raise RuntimeError(
                f"No data collected!\n"
                f"All {len(coins)} coins failed.\n"
                f"RECOMMENDATION: Check API status and network connection"
            )

        # Step 4: Save to CSV
        self.logger.info("Step 4: Saving data...")

        df = pd.DataFrame(self.collected_data)

        # Sort by date, symbol
        df = df.sort_values(['date', 'symbol'])

        # Generate output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"market_cap_{timestamp}.csv"

        df.to_csv(output_file, index=False)

        file_size_mb = output_file.stat().st_size / (1024 * 1024)

        self.logger.info(f"✅ Saved to: {output_file}")
        self.logger.info(f"  Records: {len(df):,}")
        self.logger.info(f"  File size: {file_size_mb:.1f} MB")
        self.logger.info(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        self.logger.info(f"  Unique coins: {df['symbol'].nunique()}")
        self.logger.info("")

        # Step 5: Collection summary
        collection_time_minutes = (datetime.now() - self.start_time).total_seconds() / 60

        self.logger.info("="*60)
        self.logger.info("COLLECTION SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Coins requested:    {len(coins)}")
        self.logger.info(f"Coins collected:    {df['symbol'].nunique()}")
        self.logger.info(f"Coins failed:       {len(failed_coins)}")
        self.logger.info(f"Total records:      {len(df):,}")
        self.logger.info(f"API calls made:     {self.api_calls_made}")
        self.logger.info(f"Collection time:    {collection_time_minutes:.1f} minutes")
        self.logger.info(f"Output file:        {output_file}")
        self.logger.info("")

        if failed_coins:
            self.logger.warning(f"⚠️  {len(failed_coins)} coins failed:")
            for coin in failed_coins[:10]:  # Show first 10
                self.logger.warning(f"  - {coin['id']} ({coin['symbol']}): {coin['error'][:100]}")
            if len(failed_coins) > 10:
                self.logger.warning(f"  ... and {len(failed_coins) - 10} more")
            self.logger.info("")

        self.logger.info("NEXT STEPS:")
        self.logger.info(f"  1. Validate data: uv run validation/scripts/validate_coingecko.py {output_file}")
        self.logger.info("  2. Merge with crypto2: uv run tools/merge_datasets.py")
        self.logger.info("")
        self.logger.info("Collection complete! 🚀")

        return str(output_file)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect historical market cap data from CoinGecko free API'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=500,
        help='Number of top coins to collect (default: 500)'
    )
    parser.add_argument(
        '--output',
        default='data/raw/coingecko',
        help='Output directory (default: data/raw/coingecko)'
    )
    parser.add_argument(
        '--api-key',
        help='CoinGecko Demo API key (optional but recommended)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: only collect 3 coins'
    )
    parser.add_argument(
        '--delay',
        type=float,
        help='Override rate limit delay in seconds (e.g., 20.0 for no-API-key usage)'
    )

    args = parser.parse_args()

    # Get API key from environment if not provided
    api_key = args.api_key or os.getenv('COINGECKO_API_KEY')

    if not api_key:
        print("⚠️  No API key provided (using free tier without registration)")
        print("   Consider registering for Demo API for better rate limits:")
        print("   https://www.coingecko.com/en/api")
        print("")

    try:
        collector = CoinGeckoCollector(api_key=api_key, output_dir=args.output, delay_override=args.delay)
        output_file = collector.run_collection(top_n=args.top_n, test_mode=args.test)

        print("")
        print("✅ Collection successful!")
        print(f"   Output: {output_file}")
        return 0

    except Exception as e:
        print("")
        print("="*60)
        print("COLLECTION FAILED")
        print("="*60)
        print(f"Error: {e}")
        print("")
        return 1


if __name__ == '__main__':
    sys.exit(main())
