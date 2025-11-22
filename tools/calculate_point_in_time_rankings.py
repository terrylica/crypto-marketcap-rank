#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pandas>=2.1.0",
#   "pyarrow>=14.0.0",
# ]
# ///
"""
Calculate point-in-time historical rankings from crypto2 data.

This demonstrates TRUE point-in-time rankings:
- On 2024-01-15, what was Bitcoin's rank THAT day?
- Not: What are today's top coins historically?

Shows rankings for specific dates to prove we understand the requirement.
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


def calculate_rankings_for_date(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """
    Calculate rankings for a specific date based on market_cap.

    Args:
        df: DataFrame with columns: timestamp, symbol, name, market_cap
        date: Date string in YYYY-MM-DD format

    Returns:
        DataFrame with rankings for that date, sorted by rank
    """
    # Extract date from timestamp (format: "2013-07-26 23:59:59" -> "2013-07-26")
    df['date'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d')

    # Filter to specific date
    date_data = df[df['date'] == date].copy()

    if len(date_data) == 0:
        print(f"⚠️  No data for {date}")
        return pd.DataFrame()

    # Sort by market_cap descending and assign rank
    date_data = date_data.sort_values('market_cap', ascending=False).reset_index(drop=True)
    date_data['rank'] = range(1, len(date_data) + 1)

    # Select relevant columns
    result = date_data[['rank', 'symbol', 'name', 'market_cap', 'circulating_supply']].copy()

    # Format market_cap for readability
    result['market_cap_formatted'] = result['market_cap'].apply(
        lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
    )

    return result


def main():
    # Load crypto2 data
    data_file = Path("data/raw/crypto2/scenario_b_full_20251120_20251120_154741.csv")

    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        sys.exit(1)

    print(f"📂 Loading data from: {data_file}")
    df = pd.read_csv(data_file)

    print(f"✅ Loaded {len(df):,} records")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   Unique coins: {df['symbol'].nunique()}")

    # Example dates to show point-in-time rankings
    example_dates = [
        "2013-07-26",  # Very early crypto (Bitcoin only era)
        "2015-01-01",  # Early altcoin era
        "2017-12-17",  # First major bull run peak
        "2021-11-10",  # 2021 bull run peak
        "2024-01-01",  # Recent
        "2024-11-20",  # Most recent available
    ]

    print("\n" + "="*80)
    print("POINT-IN-TIME HISTORICAL RANKINGS")
    print("="*80)

    for date in example_dates:
        rankings = calculate_rankings_for_date(df, date)

        if len(rankings) == 0:
            continue

        print(f"\n📅 {date}")
        print("-" * 80)
        print(f"{'Rank':<6} {'Symbol':<10} {'Name':<25} {'Market Cap':>20}")
        print("-" * 80)

        # Show top 10 for that date
        for _, row in rankings.head(10).iterrows():
            print(f"{int(row['rank']):<6} {row['symbol']:<10} {row['name']:<25} {row['market_cap_formatted']:>20}")

        if len(rankings) > 10:
            print(f"   ... and {len(rankings) - 10} more coins")

    # Save full rankings for a specific date as example
    example_date = "2024-11-20"
    rankings = calculate_rankings_for_date(df, example_date)

    if len(rankings) > 0:
        output_file = Path(f"data/analysis/point_in_time_rankings_{example_date}.csv")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        rankings.to_csv(output_file, index=False)
        print(f"\n✅ Saved full rankings for {example_date} to: {output_file}")

    print("\n" + "="*80)
    print("KEY INSIGHT: This is POINT-IN-TIME ranking")
    print("="*80)
    print("Each date shows what the rankings were THAT day, not retroactive.")
    print("For example, if a coin was #5 on 2017-12-17 but dead today, it still shows as #5.")
    print("\nTo get more comprehensive rankings, we need to collect more coins' historical data.")
    print(f"Currently have: {df['symbol'].nunique()} coins")
    print(f"Available in CoinGecko: 19,410 coins (see data/coin_ids/)")


if __name__ == "__main__":
    main()
