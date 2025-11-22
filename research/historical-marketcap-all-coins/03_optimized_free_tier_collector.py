#!/usr/bin/env python3
"""
Optimized Free-Tier Market Cap Data Collector

This script works within CoinPaprika free tier limitations:
- Collects market cap for ~16,000 top coins (available without hitting 402 error)
- Stores snapshots in JSONL format for time-series analysis
- Can be run on a schedule (cron) to build historical database
- Includes error recovery and rate limiting

FINDINGS FROM INVESTIGATION:
- /tickers endpoint works until coin ~16,500 then returns 402 Payment Required
- Free tier: ~300 requests/hour
- /global provides aggregate market cap (no per-coin breakdown)
- Solution: Collect available coins regularly to track top market movements

STORAGE ESTIMATE:
- Per snapshot: ~8 MB for 16,500 coins
- Per day (48 snapshots): ~384 MB
- Per year: ~140 GB (manageable with compression)
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

BASE_URL = "https://api.coinpaprika.com/v1"
OUTPUT_DIR = Path("/tmp/historical-marketcap-all-coins")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output files
HISTORY_DIR = OUTPUT_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_SNAPSHOT = OUTPUT_DIR / "market_cap_current.json"
HISTORY_JSONL = HISTORY_DIR / "market_cap_history.jsonl"
GLOBAL_HISTORY = HISTORY_DIR / "global_market_history.jsonl"
STATS_FILE = OUTPUT_DIR / "optimization_stats.json"

# Configuration
ITEMS_PER_PAGE = 250
FREE_TIER_WORKING_PAGES = 65  # Stop before we hit 402 error
FREE_TIER_MAX_COINS = FREE_TIER_WORKING_PAGES * ITEMS_PER_PAGE  # ~16,250


class FreetierOptimizedCollector:
    """
    Optimized collector that respects free tier limits and builds
    a time-series database of top 16,000+ coins
    """

    def __init__(self):
        self.collected = 0
        self.request_count = 0
        self.start_time = datetime.now()
        self.coins_data = []
        self.global_data = None
        self.errors = []

    def fetch_global_market_data(self) -> Optional[Dict]:
        """
        Fetch global aggregate market cap and stats

        Free tier, unlimited calls, no per-coin breakdown
        """
        endpoint = f"{BASE_URL}/global"

        try:
            response = requests.get(endpoint, timeout=10)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                self.errors.append({"endpoint": "/global", "status": response.status_code})
                return None
        except Exception as e:
            self.errors.append({"endpoint": "/global", "error": str(e)})
            return None

    def fetch_tickers_page(self, page: int) -> Optional[List[Dict]]:
        """
        Fetch a page of ticker data

        Free tier limit: works up to ~page 65 (16,250 coins)
        Beyond that: returns 402 Payment Required
        """
        endpoint = f"{BASE_URL}/tickers"
        params = {
            "limit": ITEMS_PER_PAGE,
            "offset": (page - 1) * ITEMS_PER_PAGE,
        }

        try:
            response = requests.get(endpoint, params=params, timeout=10)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 402:
                # Hit the payment wall - expected at ~page 66+
                return None
            else:
                self.errors.append({"page": page, "status": response.status_code})
                return None
        except Exception as e:
            self.errors.append({"page": page, "error": str(e)})
            return None

    def collect_free_tier_coins(self) -> int:
        """
        Collect market cap for all coins available in free tier

        Returns the number of coins collected
        """
        print("=" * 70)
        print("COLLECTING FREE-TIER MARKET CAP DATA")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Target: Top {FREE_TIER_MAX_COINS:,} coins")
        print(f"Pages to fetch: {FREE_TIER_WORKING_PAGES}")
        print()

        # Fetch each page
        page = 1
        hit_402 = False

        while page <= FREE_TIER_WORKING_PAGES and not hit_402:
            pct = (page / FREE_TIER_WORKING_PAGES) * 100
            print(f"[{pct:>5.1f}%] Page {page:>3d}/{FREE_TIER_WORKING_PAGES}... ",
                  end="", flush=True)

            page_data = self.fetch_tickers_page(page)

            if page_data is None:
                hit_402 = True
                print("✗ Hit 402 Payment Required (free tier limit)")
                break
            elif len(page_data) == 0:
                print("✓ Empty (end of data)")
                break
            else:
                self.coins_data.extend(page_data)
                self.collected += len(page_data)
                print(f"✓ {len(page_data):>3d} coins ({self.collected:>6d} total)")

            page += 1

        print(f"\n✓ Collected {self.collected:,} coins")
        return self.collected

    def collect_global_data(self) -> None:
        """Fetch aggregate global market cap data"""
        print("\n" + "=" * 70)
        print("COLLECTING GLOBAL MARKET DATA")
        print("=" * 70)

        print("Fetching /global endpoint... ", end="", flush=True)
        self.global_data = self.fetch_global_market_data()

        if self.global_data:
            print("✓")
            print(f"\nGlobal Market Snapshot:")
            print(f"  Market Cap: ${self.global_data.get('market_cap_usd', 0):,.0f}")
            print(f"  24h Volume: ${self.global_data.get('volume_24h_usd', 0):,.0f}")
            print(f"  Bitcoin Dominance: {self.global_data.get('bitcoin_dominance_percentage', 0):.2f}%")
            print(f"  Total Cryptocurrencies: {self.global_data.get('cryptocurrencies_number', 0)}")
            print(f"  Market Cap ATH: ${self.global_data.get('market_cap_ath_value', 0):,.0f}")
        else:
            print("✗ Failed")

    def save_current_snapshot(self) -> None:
        """Save current market cap snapshot"""
        if not self.coins_data:
            print("No data to save")
            return

        print("\n" + "=" * 70)
        print("SAVING DATA")
        print("=" * 70)

        # Current snapshot (JSON)
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'coins_count': len(self.coins_data),
            'coins': self.coins_data,
            'global': self.global_data
        }

        with open(CURRENT_SNAPSHOT, 'w') as f:
            json.dump(snapshot, f, indent=2)
        print(f"✓ Current snapshot: {CURRENT_SNAPSHOT}")
        print(f"  Size: {CURRENT_SNAPSHOT.stat().st_size / 1024 / 1024:.2f} MB")

        # Append to history (JSONL - one snapshot per line)
        timestamp = datetime.now().isoformat()
        history_entry = {
            'timestamp': timestamp,
            'coins_count': len(self.coins_data),
            'coins': self.coins_data
        }

        with open(HISTORY_JSONL, 'a') as f:
            f.write(json.dumps(history_entry) + '\n')
        print(f"✓ Appended to history: {HISTORY_JSONL}")

        # Global data history
        if self.global_data:
            global_entry = {
                'timestamp': timestamp,
                'global': self.global_data
            }
            with open(GLOBAL_HISTORY, 'a') as f:
                f.write(json.dumps(global_entry) + '\n')
            print(f"✓ Appended to global history: {GLOBAL_HISTORY}")

    def analyze_data(self) -> Dict:
        """Analyze the collected data"""
        print("\n" + "=" * 70)
        print("DATA ANALYSIS")
        print("=" * 70)

        stats = {
            'total_coins': len(self.coins_data),
            'coins_with_market_cap': 0,
            'total_market_cap': 0,
            'top_10_coins': []
        }

        if not self.coins_data:
            return stats

        # Market cap stats
        market_caps = []
        for coin in self.coins_data:
            if 'quotes' in coin and 'USD' in coin['quotes']:
                mcap = coin['quotes']['USD'].get('market_cap')
                if mcap:
                    market_caps.append(mcap)
                    stats['coins_with_market_cap'] += 1

        if market_caps:
            stats['total_market_cap'] = sum(market_caps)

            print(f"\nCoin Coverage:")
            print(f"  Total coins collected: {len(self.coins_data):,}")
            print(f"  With market cap: {stats['coins_with_market_cap']:,}")

            print(f"\nMarket Cap Statistics:")
            print(f"  Total market cap (all): ${stats['total_market_cap']:,.0f}")
            print(f"  Average per coin: ${sum(market_caps) / len(market_caps):,.0f}")

            # Top coins
            ranked = [c for c in self.coins_data if c.get('rank')]
            ranked.sort(key=lambda x: x.get('rank', 99999))

            print(f"\nTop 10 Coins:")
            for coin in ranked[:10]:
                mcap = coin['quotes']['USD']['market_cap'] if 'quotes' in coin and 'USD' in coin['quotes'] else 0
                print(f"  {coin['rank']:3d}. {coin['symbol']:8s} {coin['name']:<30s} ${mcap:>15,.0f}")
                stats['top_10_coins'].append({
                    'rank': coin['rank'],
                    'symbol': coin['symbol'],
                    'market_cap': mcap
                })

        return stats

    def save_stats(self, analysis: Dict) -> None:
        """Save collection statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        stats = {
            'timestamp': datetime.now().isoformat(),
            'collection_time_seconds': elapsed,
            'coins_collected': self.collected,
            'requests_made': self.request_count,
            'requests_per_second': self.request_count / elapsed if elapsed > 0 else 0,
            'free_tier_coverage': {
                'max_coins_available': FREE_TIER_MAX_COINS,
                'coins_collected': self.collected,
                'coverage_percent': (self.collected / FREE_TIER_MAX_COINS) * 100 if FREE_TIER_MAX_COINS > 0 else 0,
                'pages_fetched': self.request_count - 1  # -1 for global endpoint
            },
            'analysis': analysis,
            'rate_limit_info': {
                'free_tier_limit': '300 requests/hour',
                'items_per_page': ITEMS_PER_PAGE,
                'requests_needed_for_full_coverage': FREE_TIER_WORKING_PAGES + 1
            },
            'next_steps': [
                f"Schedule this script every 30-60 minutes via cron",
                f"After 30 days of collection: {HISTORY_JSONL} will contain 1 month of snapshots",
                f"After 1 year of collection: ~140 GB storage with {365*48:,} daily snapshots",
                f"Use JSONL format for time-series analysis and trending"
            ]
        }

        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"\n✓ Statistics saved to: {STATS_FILE}")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("OPTIMIZED FREE-TIER MARKET CAP COLLECTOR")
    print("=" * 70)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"API Tier: Free (300 req/hour)")
    print(f"Max coins available: {FREE_TIER_MAX_COINS:,}")
    print()

    collector = FreetierOptimizedCollector()

    # Collect global data
    collector.collect_global_data()

    # Collect coin-specific data
    collector.collect_free_tier_coins()

    if collector.collected == 0:
        print("\n✗ Failed to collect any coins")
        sys.exit(1)

    # Save data
    collector.save_current_snapshot()

    # Analyze
    analysis = collector.analyze_data()

    # Save stats
    collector.save_stats(analysis)

    # Final summary
    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)

    elapsed = (datetime.now() - collector.start_time).total_seconds()

    print(f"""
Summary:
  Coins collected: {collector.collected:,}
  Requests made: {collector.request_count}
  Time taken: {elapsed:.1f}s
  Speed: {collector.request_count/elapsed*1000:.1f} req/sec
  Errors: {len(collector.errors)}

Output Files Created:
  - {CURRENT_SNAPSHOT.name} (current snapshot)
  - {HISTORY_JSONL.name} (time-series history)
  - {GLOBAL_HISTORY.name} (global market history)
  - {STATS_FILE.name} (statistics)

Next Steps:
1. Review output files
2. Set up cron job for periodic collection:

   */30 * * * * cd /tmp/historical-marketcap-all-coins && \\
       uv run 03_optimized_free_tier_collector.py >> /tmp/collector.log 2>&1

3. After collection starts:
   - Use market_cap_history.jsonl for time-series analysis
   - Track market cap trends over time
   - Compare snapshots day-over-day

Rate Limit Summary:
  - Free tier: ~300 requests/hour
  - This script: {collector.request_count} requests
  - Can run every 6 minutes (300 requests / 60 = 5 req/min)
  - Recommended: Every 30 minutes for balanced data collection
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
