#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""
Fetch current market cap rankings from CoinGecko.

This gets you the TOP N coins ranked by market cap RIGHT NOW.
Each coin includes: rank, id, symbol, name, market_cap

Perfect for getting a snapshot of current rankings!
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests


def fetch_current_rankings(top_n: int = 500, use_api_key: bool = True):
    """
    Fetch current top N coins ranked by market cap.

    Args:
        top_n: Number of top coins to fetch (default 500)
        use_api_key: Whether to use API key (default True)

    Returns:
        List of coin data with rankings
    """
    api_key = os.getenv('COINGECKO_API_KEY') if use_api_key else None

    # CoinGecko allows max 250 per page
    per_page = 250
    pages_needed = (top_n + per_page - 1) // per_page  # Ceiling division

    all_coins = []

    print(f"🎯 Fetching top {top_n} coins ranked by market cap...")
    print(f"   Pages needed: {pages_needed} (250 coins per page)")

    if api_key:
        print("   ✅ Using Demo API key")
        delay = 4  # 4 seconds between calls
    else:
        print("   ⚠️  No API key (using free tier)")
        delay = 20  # 20 seconds between calls

    for page in range(1, pages_needed + 1):
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': per_page,
            'page': page,
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }

        if api_key:
            params['x_cg_demo_api_key'] = api_key

        print(f"\n📄 Page {page}/{pages_needed}: Fetching coins rank {(page-1)*per_page + 1} to {min(page*per_page, top_n)}...")

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                print("   ⚠️  Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                break

            coins = response.json()
            all_coins.extend(coins)

            print(f"   ✅ Fetched {len(coins)} coins")
            print(f"      Sample: #{coins[0]['market_cap_rank']} {coins[0]['symbol'].upper()} = ${coins[0]['market_cap']:,.0f}")

            # Wait between requests (except after last page)
            if page < pages_needed:
                print(f"   ⏳ Waiting {delay}s before next request...")
                time.sleep(delay)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            break

    # Trim to exact top_n
    all_coins = all_coins[:top_n]

    print(f"\n✅ Total fetched: {len(all_coins)} coins")
    return all_coins


def save_rankings(coins, output_dir: str = "data/rankings"):
    """
    Save rankings to JSON and CSV files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Save full JSON
    json_file = output_path / f"current_rankings_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(coins, f, indent=2)
    print(f"\n💾 Saved full data to: {json_file}")

    # Save simplified CSV (rank, id, symbol, name, market_cap)
    csv_file = output_path / f"current_rankings_{timestamp}.csv"
    with open(csv_file, 'w') as f:
        f.write("rank,id,symbol,name,market_cap,price,volume_24h\n")
        for coin in coins:
            f.write(f"{coin['market_cap_rank']},{coin['id']},{coin['symbol']},{coin['name']},{coin['market_cap']},{coin['current_price']},{coin['total_volume']}\n")
    print(f"💾 Saved CSV to: {csv_file}")

    # Save summary
    summary = {
        "date": date_str,
        "timestamp": timestamp,
        "total_coins": len(coins),
        "top_10": [
            {
                "rank": coin['market_cap_rank'],
                "id": coin['id'],
                "symbol": coin['symbol'],
                "name": coin['name'],
                "market_cap": coin['market_cap']
            }
            for coin in coins[:10]
        ]
    }

    summary_file = output_path / f"summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Saved summary to: {summary_file}")

    return json_file, csv_file, summary_file


def main():
    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "all":
            top_n = 13000  # Maximum ranked coins on CoinGecko
            print("="*80)
            print("FETCH ALL RANKED COINS (~13,000 coins)")
            print("="*80)
        else:
            top_n = int(sys.argv[1])
            print("="*80)
            print(f"FETCH CURRENT MARKET CAP RANKINGS - TOP {top_n} COINS")
            print("="*80)
    else:
        top_n = 500
        print("="*80)
        print(f"FETCH CURRENT MARKET CAP RANKINGS - TOP {top_n} COINS")
        print("="*80)

    # Fetch rankings
    coins = fetch_current_rankings(top_n=top_n)

    if not coins:
        print("\n❌ No data fetched!")
        sys.exit(1)

    # Save results
    json_file, csv_file, summary_file = save_rankings(coins)

    # Display top 20
    print("\n" + "="*80)
    print("TOP 20 COINS BY MARKET CAP (RIGHT NOW)")
    print("="*80)
    print(f"{'Rank':<6} {'ID':<20} {'Symbol':<10} {'Market Cap':>20}")
    print("-"*80)

    for coin in coins[:20]:
        print(f"{coin['market_cap_rank']:<6} {coin['id']:<20} {coin['symbol'].upper():<10} ${coin['market_cap']:>19,.0f}")

    if len(coins) > 20:
        print(f"\n... and {len(coins) - 20} more coins")

    print("\n" + "="*80)
    print("KEY FEATURES OF THIS DATA")
    print("="*80)
    print("✅ CURRENT rankings (real-time snapshot)")
    print("✅ Includes market_cap_rank for each coin")
    print("✅ Includes coin ID (can map to our 19,410 coin IDs)")
    print("✅ Includes market_cap value")
    print(f"✅ Fast: {(top_n + 249) // 250} API calls for top {top_n}")
    print("✅ Works without API key (just slower)")
    print("\n💡 TIP: Use 'all' to fetch ALL ~13,000 ranked coins:")
    print("   uv run tools/fetch_current_rankings.py all")
    print("\n❌ LIMITATION: This is CURRENT rankings only, not historical")
    print("   For historical rankings, we still need to collect market_cap data")
    print("   for each date and calculate rankings ourselves.")

    print("\n" + "="*80)
    print("📊 Files saved in: data/rankings/")
    print("="*80)


if __name__ == "__main__":
    main()
