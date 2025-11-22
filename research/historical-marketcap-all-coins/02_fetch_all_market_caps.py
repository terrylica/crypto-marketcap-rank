#!/usr/bin/env python3
"""
Fetch market cap data for ALL coins using paginated /tickers endpoint

This script fetches current market cap data for all 56,500+ coins using the
/tickers endpoint with pagination. Each request returns up to 250 coins,
requiring ~227 requests for complete coverage.

Key data collected:
- Coin ID
- Market Cap (USD)
- Price (USD)
- 24h Volume
- Market Cap Rank
- 24h % Change
- Timestamp of collection
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
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

BASE_URL = "https://api.coinpaprika.com/v1"
OUTPUT_DIR = Path("/tmp/historical-marketcap-all-coins")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output files
MARKET_CAP_SNAPSHOT_FILE = OUTPUT_DIR / "market_cap_snapshot.jsonl"
MARKET_CAP_JSON_FILE = OUTPUT_DIR / "market_cap_snapshot.json"
MARKET_CAP_CSV_FILE = OUTPUT_DIR / "market_cap_snapshot.csv"
STATS_FILE = OUTPUT_DIR / "collection_stats.json"

# Rate limiting
REQUESTS_PER_HOUR = 300
ITEMS_PER_PAGE = 250


class MarketCapCollector:
    """Collect market cap data for all coins with rate limiting and progress tracking"""

    def __init__(self):
        self.collected = 0
        self.failed = 0
        self.request_count = 0
        self.start_time = datetime.now()
        self.data = []
        self.errors = []

    def fetch_page(self, page: int) -> Optional[List[Dict]]:
        """
        Fetch a single page of ticker data

        Args:
            page: Page number (starting from 1)

        Returns:
            List of coin data or None if request fails
        """
        endpoint = f"{BASE_URL}/tickers"
        params = {
            "limit": ITEMS_PER_PAGE,
            "offset": (page - 1) * ITEMS_PER_PAGE,
        }

        try:
            response = requests.get(endpoint, params=params, timeout=30)
            self.request_count += 1

            if response.status_code == 200:
                data = response.json()
                return data
            elif response.status_code == 429:
                print(f"  ⚠ Rate limited (429). Please wait before retrying.")
                return None
            else:
                error_msg = f"Status {response.status_code}"
                self.errors.append({"page": page, "error": error_msg})
                print(f"  ✗ Page {page}: {error_msg}")
                return None

        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            self.errors.append({"page": page, "error": error_msg})
            print(f"  ✗ Page {page}: {error_msg}")
            return None
        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {e}"
            self.errors.append({"page": page, "error": error_msg})
            print(f"  ✗ Page {page}: {error_msg}")
            return None
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            self.errors.append({"page": page, "error": error_msg})
            print(f"  ✗ Page {page}: {error_msg}")
            return None

    def fetch_all_market_caps(self, max_pages: Optional[int] = None) -> bool:
        """
        Fetch market cap data for all coins with pagination

        Args:
            max_pages: Maximum pages to fetch (for testing). None = fetch all

        Returns:
            True if successful, False otherwise
        """
        print("=" * 70)
        print("FETCHING MARKET CAP DATA FOR ALL COINS")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Endpoint: {BASE_URL}/tickers")
        print(f"Items per page: {ITEMS_PER_PAGE}")
        print()

        # Estimate total pages needed
        # Based on ~56,559 total coins
        estimated_pages = (56559 // ITEMS_PER_PAGE) + 1
        if max_pages:
            estimated_pages = min(max_pages, estimated_pages)

        print(f"Estimated pages to fetch: {estimated_pages}")
        print()

        # Fetch all pages
        page = 1
        consecutive_empty = 0

        while True:
            if max_pages and page > max_pages:
                print(f"\nReached max_pages limit ({max_pages})")
                break

            # Show progress
            pct = min(100, (page / estimated_pages) * 100)
            print(f"[{pct:>5.1f}%] Fetching page {page:>4d}... ", end="", flush=True)

            # Fetch page
            page_data = self.fetch_page(page)

            if page_data is None:
                # Network error
                self.failed += 1
                print("✗ FAILED")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    print(f"\n✗ 3 consecutive failures. Stopping.")
                    break
            elif len(page_data) == 0:
                # Empty result set = we've reached the end
                print(f"✓ Empty (end of data)")
                print(f"\n✓ Reached end at page {page}")
                break
            else:
                # Success
                consecutive_empty = 0
                self.collected += len(page_data)
                self.data.extend(page_data)
                print(f"✓ Got {len(page_data):>4d} coins ({self.collected:>6d} total)")

            page += 1

        return len(self.data) > 0

    def save_data(self) -> None:
        """Save collected data in multiple formats"""
        if not self.data:
            print("No data to save")
            return

        print("\n" + "=" * 70)
        print("SAVING DATA")
        print("=" * 70)

        # JSON format (complete data)
        with open(MARKET_CAP_JSON_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
        print(f"✓ Saved JSON: {MARKET_CAP_JSON_FILE}")
        print(f"  Size: {MARKET_CAP_JSON_FILE.stat().st_size / 1024 / 1024:.2f} MB")

        # JSONL format (one record per line - efficient for streaming)
        with open(MARKET_CAP_SNAPSHOT_FILE, 'w') as f:
            for record in self.data:
                record['timestamp'] = datetime.now().isoformat()
                f.write(json.dumps(record) + '\n')
        print(f"✓ Saved JSONL: {MARKET_CAP_SNAPSHOT_FILE}")
        print(f"  Size: {MARKET_CAP_SNAPSHOT_FILE.stat().st_size / 1024 / 1024:.2f} MB")

        # CSV format (for spreadsheets)
        import csv
        try:
            with open(MARKET_CAP_CSV_FILE, 'w', newline='') as f:
                if self.data:
                    # Extract relevant fields from first record
                    first = self.data[0]
                    fieldnames = ['id', 'symbol', 'name', 'rank']

                    # Add USD quote fields if present
                    if 'quotes' in first and 'USD' in first['quotes']:
                        fieldnames.extend([
                            'price_usd',
                            'market_cap_usd',
                            'market_cap_change_24h',
                            'volume_24h',
                            'percent_change_24h'
                        ])

                    fieldnames.append('timestamp')

                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    timestamp = datetime.now().isoformat()
                    for record in self.data:
                        row = {
                            'id': record.get('id'),
                            'symbol': record.get('symbol'),
                            'name': record.get('name'),
                            'rank': record.get('rank'),
                            'timestamp': timestamp
                        }

                        # Add USD quote fields
                        if 'quotes' in record and 'USD' in record['quotes']:
                            usd = record['quotes']['USD']
                            row.update({
                                'price_usd': usd.get('price'),
                                'market_cap_usd': usd.get('market_cap'),
                                'market_cap_change_24h': usd.get('market_cap_change_24h'),
                                'volume_24h': usd.get('volume_24h'),
                                'percent_change_24h': usd.get('percent_change_24h')
                            })

                        writer.writerow(row)

            print(f"✓ Saved CSV: {MARKET_CAP_CSV_FILE}")
            print(f"  Size: {MARKET_CAP_CSV_FILE.stat().st_size / 1024 / 1024:.2f} MB")
        except Exception as e:
            print(f"✗ Failed to save CSV: {e}")

    def analyze_data(self) -> Dict:
        """Analyze collected market cap data"""
        print("\n" + "=" * 70)
        print("DATA ANALYSIS")
        print("=" * 70)

        if not self.data:
            print("No data to analyze")
            return {}

        # Basic stats
        print(f"\nTotal Records: {len(self.data):,}")

        # Market cap stats
        market_caps = []
        for record in self.data:
            if 'quotes' in record and 'USD' in record['quotes']:
                mcap = record['quotes']['USD'].get('market_cap')
                if mcap is not None:
                    market_caps.append(mcap)

        if market_caps:
            market_caps.sort(reverse=True)
            total_mcap = sum(market_caps)
            print(f"\nMarket Cap Data:")
            print(f"  Total Market Cap: ${total_mcap:,.0f}")
            print(f"  Average Market Cap: ${sum(market_caps) / len(market_caps):,.0f}")
            print(f"  Median Market Cap: ${market_caps[len(market_caps)//2]:,.0f}")
            print(f"  Largest: ${market_caps[0]:,.0f}")
            print(f"  Smallest: ${market_caps[-1]:,.0f}")

        # Coins with market cap
        coins_with_mcap = sum(1 for r in self.data
                             if 'quotes' in r and 'USD' in r['quotes']
                             and r['quotes']['USD'].get('market_cap') is not None)
        print(f"\nCoin Coverage:")
        print(f"  Total coins: {len(self.data):,}")
        print(f"  With market cap: {coins_with_mcap:,} ({coins_with_mcap/len(self.data)*100:.1f}%)")

        # Top coins
        ranked = [r for r in self.data if r.get('rank') is not None]
        ranked.sort(key=lambda x: x.get('rank', 99999))

        print(f"\nTop 10 Coins by Market Cap Rank:")
        for coin in ranked[:10]:
            mcap = None
            if 'quotes' in coin and 'USD' in coin['quotes']:
                mcap = coin['quotes']['USD'].get('market_cap')

            mcap_str = f"${mcap:,.0f}" if mcap else "N/A"
            print(f"  Rank {coin['rank']:4d}: {coin['symbol']:8s} - {mcap_str}")

        return {
            'total_records': len(self.data),
            'total_market_cap': sum(market_caps) if market_caps else 0,
            'coins_with_market_cap': coins_with_mcap,
            'requests_made': self.request_count,
            'errors': len(self.errors)
        }

    def save_stats(self, analysis: Dict) -> None:
        """Save collection statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        stats = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': elapsed,
            'total_coins_collected': self.collected,
            'failed_coins': self.failed,
            'requests_made': self.request_count,
            'errors': len(self.errors),
            'analysis': analysis,
            'rate_limit_info': {
                'free_tier_limit': f"{REQUESTS_PER_HOUR} requests/hour",
                'items_per_page': ITEMS_PER_PAGE,
                'estimated_requests_for_full': (56559 // ITEMS_PER_PAGE) + 1
            }
        }

        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"\n✓ Saved statistics to: {STATS_FILE}")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("COINPAPRIKA - ALL COINS MARKET CAP FETCHER")
    print("=" * 70)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()

    # Create collector
    collector = MarketCapCollector()

    # Fetch all market cap data
    # NOTE: To test, use max_pages=2 for quick test
    # For production: remove max_pages parameter
    success = collector.fetch_all_market_caps(max_pages=None)

    if not success:
        print("\n✗ Failed to fetch any market cap data")
        sys.exit(1)

    # Save data
    collector.save_data()

    # Analyze
    analysis = collector.analyze_data()

    # Save stats
    collector.save_stats(analysis)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    elapsed = (datetime.now() - collector.start_time).total_seconds()

    print(f"""
✓ Collection Complete

Data Collected:
  - Total coins: {collector.collected:,}
  - Requests made: {collector.request_count}
  - Time taken: {elapsed:.1f}s
  - Average speed: {collector.request_count/elapsed*1000:.1f} req/sec
  - Errors: {len(collector.errors)}

Output Files:
  - {MARKET_CAP_JSON_FILE.name}
  - {MARKET_CAP_SNAPSHOT_FILE.name}
  - {MARKET_CAP_CSV_FILE.name}
  - {STATS_FILE.name}

Next Steps:
1. Verify data in output files
2. Create cron job to collect periodically
3. Build historical database from snapshots
""")
    print("=" * 70)


if __name__ == "__main__":
    main()
