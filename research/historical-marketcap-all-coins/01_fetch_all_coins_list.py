#!/usr/bin/env python3
"""
Fetch the complete list of ALL available coins from CoinPaprika API

This script retrieves the full list of 13,500+ cryptocurrencies and their metadata
to serve as the foundation for mass market cap data collection.

Key data collected:
- Coin ID (for API calls)
- Symbol
- Name
- Rank
- Total supply
- Active markets count
"""
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///

import requests
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_URL = "https://api.coinpaprika.com/v1"
OUTPUT_DIR = Path("/tmp/historical-marketcap-all-coins")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COINS_METADATA_FILE = OUTPUT_DIR / "coins_metadata.json"
COINS_LIST_FILE = OUTPUT_DIR / "coins_list.txt"


def fetch_all_coins_metadata():
    """
    Fetch metadata for ALL coins from the /coins endpoint.

    This endpoint returns basic coin information:
    - id: Unique identifier (used in API calls)
    - name: Full name
    - symbol: Ticker symbol
    - rank: Market cap rank
    - is_new: Whether coin is new
    - is_active: Whether coin is active
    - type: Type of asset
    """
    print("=" * 70)
    print("FETCHING COMPLETE COIN LIST")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Target: {BASE_URL}/coins")
    print()

    endpoint = f"{BASE_URL}/coins"

    try:
        print("Making request to /coins endpoint...")
        response = requests.get(endpoint, timeout=30)

        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.3f}s")
        print(f"Response Size: {len(response.text):,} bytes")

        if response.status_code == 200:
            coins_data = response.json()

            print(f"\n✓ SUCCESS: Retrieved {len(coins_data):,} coins")

            # Save complete metadata
            with open(COINS_METADATA_FILE, 'w') as f:
                json.dump(coins_data, f, indent=2)
            print(f"✓ Saved metadata to: {COINS_METADATA_FILE}")

            # Create simple list for reference
            coin_ids = [coin['id'] for coin in coins_data]
            coin_symbols = [(coin['id'], coin['symbol'], coin['name'])
                           for coin in coins_data]

            with open(COINS_LIST_FILE, 'w') as f:
                for coin_id, symbol, name in coin_symbols:
                    f.write(f"{coin_id:<25} {symbol:<10} {name}\n")
            print(f"✓ Saved simple list to: {COINS_LIST_FILE}")

            return coins_data

        else:
            print(f"✗ ERROR: Status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None

    except requests.exceptions.Timeout:
        print("✗ ERROR: Request timed out after 30s")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"✗ ERROR: Connection failed: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ ERROR: Failed to parse JSON response: {e}")
        return None
    except Exception as e:
        print(f"✗ ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_coins_data(coins_data):
    """
    Analyze the fetched coins data and provide statistics
    """
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    if not coins_data:
        print("No data to analyze")
        return

    # Basic stats
    print(f"\nTotal Coins: {len(coins_data):,}")

    # Active coins
    active = sum(1 for coin in coins_data if coin.get('is_active', False))
    print(f"Active Coins: {active:,}")

    # Ranked coins (coins with market cap rank)
    ranked = sum(1 for coin in coins_data if coin.get('rank') is not None)
    print(f"Ranked Coins: {ranked:,}")

    # By type
    types = {}
    for coin in coins_data:
        coin_type = coin.get('type', 'unknown')
        types[coin_type] = types.get(coin_type, 0) + 1

    print(f"\nCoins by Type:")
    for coin_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {coin_type}: {count:,}")

    # Rank distribution
    print(f"\nRank Distribution:")
    print(f"  Top 10: {sum(1 for coin in coins_data if coin.get('rank', 99999) <= 10):,}")
    print(f"  Top 100: {sum(1 for coin in coins_data if coin.get('rank', 99999) <= 100):,}")
    print(f"  Top 1,000: {sum(1 for coin in coins_data if coin.get('rank', 99999) <= 1000):,}")
    print(f"  Top 10,000: {sum(1 for coin in coins_data if coin.get('rank', 99999) <= 10000):,}")

    # Sample coins
    print(f"\nSample Coins (First 5 by Rank):")
    ranked_coins = sorted([c for c in coins_data if c.get('rank')],
                         key=lambda x: x['rank'])[:5]
    for coin in ranked_coins:
        print(f"  Rank {coin['rank']:4d}: {coin['symbol']:8s} {coin['name']}")

    return {
        'total': len(coins_data),
        'active': active,
        'ranked': ranked,
        'types': types
    }


def verify_data_structure(coins_data):
    """
    Verify that the data structure is correct for mass collection
    """
    print("\n" + "=" * 70)
    print("DATA STRUCTURE VERIFICATION")
    print("=" * 70)

    if not coins_data or len(coins_data) == 0:
        print("✗ No data to verify")
        return False

    # Check first coin
    sample_coin = coins_data[0]
    required_fields = ['id', 'symbol', 'name']

    print("\nSample Coin Data:")
    print(f"  ID: {sample_coin.get('id')}")
    print(f"  Symbol: {sample_coin.get('symbol')}")
    print(f"  Name: {sample_coin.get('name')}")
    print(f"  Rank: {sample_coin.get('rank')}")
    print(f"  Active: {sample_coin.get('is_active')}")
    print(f"  Type: {sample_coin.get('type')}")

    print("\nField Coverage:")
    all_fields = set()
    for coin in coins_data:
        all_fields.update(coin.keys())

    for field in sorted(all_fields):
        count = sum(1 for coin in coins_data if field in coin)
        pct = (count / len(coins_data)) * 100
        print(f"  {field:<25} {count:>8,} coins ({pct:>5.1f}%)")

    # Verify all have IDs
    missing_id = sum(1 for coin in coins_data if 'id' not in coin)
    if missing_id == 0:
        print(f"\n✓ All {len(coins_data):,} coins have ID field")
        return True
    else:
        print(f"\n✗ {missing_id:,} coins missing ID field")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COINPAPRIKA - COMPLETE COIN LIST FETCHER")
    print("=" * 70)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()

    # Fetch all coins
    coins_data = fetch_all_coins_metadata()

    if coins_data:
        # Analyze the data
        stats = analyze_coins_data(coins_data)

        # Verify structure
        is_valid = verify_data_structure(coins_data)

        # Final summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"""
✓ Successfully fetched {len(coins_data):,} coins
✓ Data saved to {COINS_METADATA_FILE}
✓ List saved to {COINS_LIST_FILE}
✓ Data validation: {'PASSED' if is_valid else 'FAILED'}

Next Steps:
1. Review coins_metadata.json to understand the complete dataset
2. Use coins_list.txt as reference for coin IDs
3. Create market cap collection script targeting these coins

Rate Limit Info:
- Free tier: ~300 requests/hour
- To fetch market cap for all {len(coins_data):,} coins:
  - Using /tickers endpoint: 1 request per page (with pagination)
  - Estimated cost: {(len(coins_data) // 250) + 1} requests
  - Time needed: < 5 minutes
""")
        print("=" * 70)
    else:
        print("\n✗ Failed to fetch coin list")
        sys.exit(1)
