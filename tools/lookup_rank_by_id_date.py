#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pandas>=2.1.0",
#   "pyarrow>=14.0.0",
# ]
# ///
"""
Lookup rank for a specific coin ID on a specific date.

Usage:
    uv run tools/lookup_rank_by_id_date.py bitcoin 2024-01-15
    uv run tools/lookup_rank_by_id_date.py litecoin 2017-12-17
"""

import sys
from pathlib import Path

import pandas as pd


def get_rank_for_coin_on_date(coin_id: str, date: str) -> dict:
    """
    Get rank for a specific coin on a specific date.

    Args:
        coin_id: Coin identifier (e.g., "bitcoin", "litecoin")
        date: Date in YYYY-MM-DD format

    Returns:
        Dictionary with rank info or None if not found
    """
    # Load crypto2 data
    data_file = Path("data/raw/crypto2/scenario_b_full_20251120_20251120_154741.csv")

    if not data_file.exists():
        return {"error": "Data file not found", "file": str(data_file)}

    df = pd.read_csv(data_file)

    # Map common coin names to symbols (crypto2 uses symbols not IDs)
    coin_map = {
        'bitcoin': 'BTC',
        'litecoin': 'LTC',
        'ripple': 'XRP',
        'xrp': 'XRP',
        'dogecoin': 'DOGE',
        'ethereum': 'ETH',
        'monero': 'XMR',
        'dash': 'DASH',
        'stellar': 'XLM',
        'namecoin': 'NMC',
        'peercoin': 'PPC',
        'novacoin': 'NVC',
        'feathercoin': 'FTC',
        'primecoin': 'XPM',
        'terracoin': 'TRC',
    }

    # Try to find symbol
    symbol = coin_map.get(coin_id.lower())
    if not symbol:
        # Try using coin_id directly as symbol
        symbol = coin_id.upper()

    # Extract date from timestamp
    df['date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')

    # Filter to specific date
    date_data = df[df['date'] == date].copy()

    if len(date_data) == 0:
        return {
            "error": "No data for this date",
            "date": date,
            "available_range": f"{df['date'].min()} to {df['date'].max()}",
            "total_dates": df['date'].nunique()
        }

    # Calculate rankings for this date
    date_data = date_data.sort_values('market_cap', ascending=False).reset_index(drop=True)
    date_data['rank'] = range(1, len(date_data) + 1)

    # Find the specific coin
    coin_data = date_data[date_data['symbol'] == symbol]

    if len(coin_data) == 0:
        available_coins = sorted(date_data['symbol'].unique())
        return {
            "error": "Coin not found in dataset",
            "searched_for": coin_id,
            "searched_symbol": symbol,
            "date": date,
            "available_coins": available_coins,
            "total_coins": len(available_coins)
        }

    # Return rank info
    coin_row = coin_data.iloc[0]
    return {
        "coin_id": coin_id,
        "symbol": coin_row['symbol'],
        "name": coin_row['name'],
        "date": date,
        "rank": int(coin_row['rank']),
        "market_cap": float(coin_row['market_cap']),
        "market_cap_formatted": f"${coin_row['market_cap']:,.0f}",
        "circulating_supply": float(coin_row['circulating_supply']) if pd.notna(coin_row['circulating_supply']) else None,
        "total_coins_that_day": len(date_data),
        "data_source": "crypto2 (CoinMarketCap)"
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: uv run tools/lookup_rank_by_id_date.py <coin_id> <date>")
        print("")
        print("Examples:")
        print("  uv run tools/lookup_rank_by_id_date.py bitcoin 2024-01-15")
        print("  uv run tools/lookup_rank_by_id_date.py litecoin 2017-12-17")
        print("  uv run tools/lookup_rank_by_id_date.py xrp 2021-11-10")
        print("  uv run tools/lookup_rank_by_id_date.py namecoin 2013-07-26")
        sys.exit(1)

    coin_id = sys.argv[1]
    date = sys.argv[2]

    result = get_rank_for_coin_on_date(coin_id, date)

    print("\n" + "="*80)
    print(f"RANK LOOKUP: {coin_id.upper()} on {date}")
    print("="*80)

    if "error" in result:
        print(f"\n❌ {result['error']}")
        if "available_range" in result:
            print(f"   Available date range: {result['available_range']}")
        if "available_coins" in result:
            print(f"\n   Available coins ({result['total_coins']}):")
            for i, coin in enumerate(result['available_coins'][:20], 1):
                print(f"     {i:2d}. {coin}")
            if len(result['available_coins']) > 20:
                print(f"     ... and {len(result['available_coins']) - 20} more")
    else:
        print(f"\n✅ Found: {result['name']} ({result['symbol']})")
        print(f"\n   Rank on {result['date']}: #{result['rank']}")
        print(f"   Market Cap: {result['market_cap_formatted']}")
        if result['circulating_supply']:
            print(f"   Circulating Supply: {result['circulating_supply']:,.0f}")
        print(f"   Total coins ranked that day: {result['total_coins_that_day']}")
        print(f"   Data source: {result['data_source']}")

    print("\n" + "="*80)

    # Show what percentage this rank represents
    if "rank" in result:
        percentile = (result['rank'] / result['total_coins_that_day']) * 100
        print(f"\nPercentile: Top {percentile:.1f}% of all coins on {date}")
        print("="*80)


if __name__ == "__main__":
    main()
