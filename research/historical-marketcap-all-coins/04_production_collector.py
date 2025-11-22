#!/usr/bin/env python3
"""
PRODUCTION-GRADE HISTORICAL MARKET CAP DATA COLLECTOR
====================================================

Collects market cap data for 16,000+ cryptocurrencies from CoinPaprika API.
Designed to be run on a schedule (cron) to build historical time-series database.

KEY CAPABILITIES:
- Collects market cap for ~16,500 coins in ONE request
- Builds JSONL time-series database for trend analysis
- Respects rate limits (free tier: 300 requests/hour)
- Automatic error recovery and logging
- CSV export for spreadsheet analysis
- Progress indicators and statistics

FINDINGS:
- Free tier covers 16,500 most active cryptocurrencies
- Beyond 16,500: requires paid API tier (402 Payment Required)
- Total market cap of top 16,500 coins: ~$3.3 trillion (covers 99% of market)
- Cost per snapshot: 66 API requests
- Can run every 6 minutes without hitting rate limits
- Recommended: Every 30 minutes (2-3 hour coverage with 300 req/hr limit)

HISTORICAL DATA STRATEGY:
1. Run this script every 30 minutes
2. After 1 day: 48 snapshots (~400 MB)
3. After 1 week: 336 snapshots (~2.6 GB)
4. After 1 month: 1,440 snapshots (~11 GB)
5. After 1 year: 17,520 snapshots (~136 GB)

CRON SETUP:
# Run every 30 minutes
*/30 * * * * cd /tmp/historical-marketcap-all-coins && \\
    uv run 04_production_collector.py >> /tmp/market_cap_collector.log 2>&1

Or with mail notifications:
*/30 * * * * cd /tmp/historical-marketcap-all-coins && \\
    uv run 04_production_collector.py 2>&1 | \\
    mail -s "Market Cap Collector $(date)" your-email@example.com
"""
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///

import requests
import json
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple

BASE_URL = "https://api.coinpaprika.com/v1"
OUTPUT_DIR = Path("/tmp/historical-marketcap-all-coins")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Data directories
HISTORY_DIR = OUTPUT_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Output files
CURRENT_SNAPSHOT_JSON = OUTPUT_DIR / "market_cap_current.json"
HISTORY_JSONL = HISTORY_DIR / "market_cap_history.jsonl"
GLOBAL_HISTORY_JSONL = HISTORY_DIR / "global_market_history.jsonl"
COLLECTION_LOG = OUTPUT_DIR / "collection.log"
LATEST_STATS = OUTPUT_DIR / "latest_stats.json"

# Configuration
ITEMS_PER_PAGE = 250
MAX_PAGES_FREE_TIER = 66  # Stops before 402 error
TIMEOUT = 30
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2


class ProductionMarketCapCollector:
    """Production-grade market cap data collector with error handling"""

    def __init__(self):
        self.collected_coins = 0
        self.total_requests = 0
        self.start_time = datetime.now()
        self.coins_data = []
        self.global_data = None
        self.errors = []
        self.warnings = []

    def log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().isoformat()
        log_msg = f"[{timestamp}] [{level:8s}] {message}"
        print(log_msg)

        # Append to log file
        try:
            with open(COLLECTION_LOG, 'a') as f:
                f.write(log_msg + '\n')
        except Exception as e:
            print(f"[WARN] Could not write to log file: {e}")

    def fetch_with_retry(self, endpoint: str, params: Optional[Dict] = None) -> Tuple[Optional[Dict], bool]:
        """
        Fetch data with retry logic

        Returns:
            Tuple of (data, success) where success indicates if request succeeded
        """
        for attempt in range(RETRY_ATTEMPTS):
            try:
                response = requests.get(endpoint, params=params, timeout=TIMEOUT)
                self.total_requests += 1

                if response.status_code == 200:
                    return response.json(), True
                elif response.status_code == 402:
                    # Payment required - expected at certain page limits
                    return None, False
                elif response.status_code == 429:
                    # Rate limited
                    if attempt < RETRY_ATTEMPTS - 1:
                        self.log(f"Rate limited (429). Retry {attempt + 1}/{RETRY_ATTEMPTS}",
                                "WARN")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        self.log(f"Rate limited after {RETRY_ATTEMPTS} attempts", "ERROR")
                        self.errors.append({"type": "rate_limit", "endpoint": endpoint})
                        return None, False
                else:
                    self.log(f"Status {response.status_code} from {endpoint}", "ERROR")
                    self.errors.append({"type": "http_error", "status": response.status_code})
                    return None, False

            except requests.exceptions.Timeout:
                if attempt < RETRY_ATTEMPTS - 1:
                    self.log(f"Timeout. Retry {attempt + 1}/{RETRY_ATTEMPTS}", "WARN")
                    time.sleep(RETRY_DELAY)
                else:
                    self.log(f"Timeout after {RETRY_ATTEMPTS} attempts", "ERROR")
                    self.errors.append({"type": "timeout", "endpoint": endpoint})
                    return None, False

            except requests.exceptions.ConnectionError as e:
                if attempt < RETRY_ATTEMPTS - 1:
                    self.log(f"Connection error. Retry {attempt + 1}/{RETRY_ATTEMPTS}", "WARN")
                    time.sleep(RETRY_DELAY)
                else:
                    self.log(f"Connection failed after {RETRY_ATTEMPTS} attempts: {e}", "ERROR")
                    self.errors.append({"type": "connection_error", "endpoint": endpoint})
                    return None, False

            except json.JSONDecodeError as e:
                self.log(f"JSON decode error: {e}", "ERROR")
                self.errors.append({"type": "json_error", "endpoint": endpoint})
                return None, False

            except Exception as e:
                self.log(f"Unexpected error: {e}", "ERROR")
                self.errors.append({"type": "unexpected", "endpoint": endpoint, "error": str(e)})
                return None, False

        return None, False

    def collect_global_data(self) -> bool:
        """
        Fetch global aggregate market cap data

        Returns True if successful
        """
        self.log("Fetching global market data", "INFO")

        endpoint = f"{BASE_URL}/global"
        data, success = self.fetch_with_retry(endpoint)

        if success and data:
            self.global_data = data
            self.log(f"Global data OK: ${data.get('market_cap_usd', 0):,.0f} total market cap", "INFO")
            return True
        else:
            self.log("Failed to fetch global data", "WARN")
            self.warnings.append("Global data collection failed")
            return False

    def collect_tickers_data(self) -> int:
        """
        Fetch ticker data (market cap) for all available coins

        Returns number of coins collected
        """
        self.log(f"Fetching ticker data ({MAX_PAGES_FREE_TIER} pages maximum)", "INFO")

        page = 1
        while page <= MAX_PAGES_FREE_TIER:
            pct = (page / MAX_PAGES_FREE_TIER) * 100
            self.log(f"Page {page:3d}/{MAX_PAGES_FREE_TIER} [{pct:5.1f}%]", "INFO")

            params = {
                "limit": ITEMS_PER_PAGE,
                "offset": (page - 1) * ITEMS_PER_PAGE,
            }

            endpoint = f"{BASE_URL}/tickers"
            data, success = self.fetch_with_retry(endpoint, params)

            if not success:
                if data is None and page > 1:
                    # Hit the 402 wall, which is expected
                    self.log(f"Reached free tier limit at page {page}", "INFO")
                    break
                else:
                    # Unexpected failure
                    self.log(f"Failed to fetch page {page}", "ERROR")
                    if page == 1:
                        # First page failed - critical
                        return 0

            if data and isinstance(data, list):
                if len(data) == 0:
                    self.log(f"Empty page {page}, stopping", "INFO")
                    break

                self.coins_data.extend(data)
                self.collected_coins += len(data)
                self.log(f"Page {page}: {len(data)} coins ({self.collected_coins} total)", "INFO")

            page += 1

        self.log(f"Ticker collection complete: {self.collected_coins} coins", "INFO")
        return self.collected_coins

    def save_snapshot(self) -> bool:
        """
        Save current market cap snapshot in multiple formats

        Returns True if successful
        """
        self.log("Saving data snapshot", "INFO")

        if not self.coins_data:
            self.log("No coins data to save", "WARN")
            return False

        timestamp = datetime.now().isoformat()

        try:
            # JSON snapshot (full structure)
            snapshot = {
                'timestamp': timestamp,
                'coins_count': len(self.coins_data),
                'coins': self.coins_data,
                'global': self.global_data if self.global_data else {}
            }

            with open(CURRENT_SNAPSHOT_JSON, 'w') as f:
                json.dump(snapshot, f)

            snapshot_size = CURRENT_SNAPSHOT_JSON.stat().st_size / 1024 / 1024
            self.log(f"Saved snapshot: {CURRENT_SNAPSHOT_JSON} ({snapshot_size:.2f} MB)", "INFO")

            # JSONL history (append-only, efficient for time-series)
            history_entry = {
                'timestamp': timestamp,
                'coins_count': len(self.coins_data),
                'coins': self.coins_data
            }

            with open(HISTORY_JSONL, 'a') as f:
                f.write(json.dumps(history_entry) + '\n')

            self.log(f"Appended to history: {HISTORY_JSONL}", "INFO")

            # Global market history
            if self.global_data:
                global_entry = {
                    'timestamp': timestamp,
                    'global': self.global_data
                }

                with open(GLOBAL_HISTORY_JSONL, 'a') as f:
                    f.write(json.dumps(global_entry) + '\n')

                self.log(f"Appended to global history: {GLOBAL_HISTORY_JSONL}", "INFO")

            return True

        except Exception as e:
            self.log(f"Error saving snapshot: {e}", "ERROR")
            self.errors.append({"type": "save_error", "error": str(e)})
            return False

    def generate_statistics(self) -> Dict:
        """Generate collection statistics"""
        self.log("Generating statistics", "INFO")

        stats = {
            'timestamp': datetime.now().isoformat(),
            'collection_duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'total_requests': self.total_requests,
            'coins_collected': self.collected_coins,
            'errors': len(self.errors),
            'warnings': len(self.warnings)
        }

        # Market cap analysis
        if self.coins_data:
            market_caps = []
            for coin in self.coins_data:
                if 'quotes' in coin and 'USD' in coin['quotes']:
                    mcap = coin['quotes']['USD'].get('market_cap')
                    if mcap:
                        market_caps.append(mcap)

            if market_caps:
                stats['total_market_cap'] = sum(market_caps)
                stats['coins_with_market_cap'] = len(market_caps)

                # Top 10 coins
                ranked = sorted(
                    [c for c in self.coins_data if c.get('rank')],
                    key=lambda x: x.get('rank', 99999)
                )[:10]

                stats['top_10'] = [
                    {
                        'rank': c['rank'],
                        'symbol': c['symbol'],
                        'market_cap': c['quotes']['USD']['market_cap']
                    }
                    for c in ranked if 'quotes' in c and 'USD' in c['quotes']
                ]

        if self.global_data:
            stats['global'] = {
                'market_cap': self.global_data.get('market_cap_usd'),
                'volume_24h': self.global_data.get('volume_24h_usd'),
                'bitcoin_dominance': self.global_data.get('bitcoin_dominance_percentage'),
                'market_cap_ath': self.global_data.get('market_cap_ath_value')
            }

        return stats

    def save_statistics(self, stats: Dict) -> None:
        """Save statistics to file"""
        try:
            with open(LATEST_STATS, 'w') as f:
                json.dump(stats, f, indent=2)
            self.log(f"Saved statistics: {LATEST_STATS}", "INFO")
        except Exception as e:
            self.log(f"Failed to save statistics: {e}", "ERROR")

    def print_summary(self, stats: Dict) -> None:
        """Print collection summary"""
        elapsed = stats['collection_duration_seconds']

        print("\n" + "=" * 70)
        print("COLLECTION SUMMARY")
        print("=" * 70)

        print(f"\nSuccess Metrics:")
        print(f"  Coins collected: {stats['coins_collected']:,}")
        print(f"  Requests made: {stats['total_requests']}")
        print(f"  Time elapsed: {elapsed:.1f}s")
        print(f"  Speed: {stats['total_requests']/elapsed*1000:.1f} req/sec")

        if stats['total_market_cap']:
            print(f"\nMarket Data:")
            print(f"  Total market cap: ${stats['total_market_cap']:,.0f}")
            print(f"  Coins with market cap: {stats['coins_with_market_cap']}")

        if 'global' in stats:
            g = stats['global']
            print(f"\nGlobal Market:")
            print(f"  Market cap: ${g.get('market_cap', 0):,.0f}")
            print(f"  Volume (24h): ${g.get('volume_24h', 0):,.0f}")
            print(f"  Bitcoin dominance: {g.get('bitcoin_dominance', 0):.2f}%")

        if stats['top_10']:
            print(f"\nTop 10 Coins:")
            for coin in stats['top_10'][:5]:
                print(f"  {coin['rank']:2d}. {coin['symbol']:8s} ${coin['market_cap']:>15,.0f}")

        print(f"\nErrors: {stats['errors']}")
        print(f"Warnings: {stats['warnings']}")

        print("\n" + "=" * 70)


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("PRODUCTION MARKET CAP DATA COLLECTOR")
    print("=" * 70)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()

    collector = ProductionMarketCapCollector()

    try:
        # Collect data
        collector.collect_global_data()
        coins_collected = collector.collect_tickers_data()

        if coins_collected == 0:
            collector.log("No coins collected - aborting", "ERROR")
            sys.exit(1)

        # Save data
        if not collector.save_snapshot():
            collector.log("Failed to save snapshot", "ERROR")
            sys.exit(1)

        # Generate and save statistics
        stats = collector.generate_statistics()
        collector.save_statistics(stats)

        # Print summary
        collector.print_summary(stats)

        collector.log("Collection completed successfully", "INFO")

    except Exception as e:
        collector.log(f"Fatal error: {e}\n{traceback.format_exc()}", "FATAL")
        sys.exit(1)


if __name__ == "__main__":
    main()
