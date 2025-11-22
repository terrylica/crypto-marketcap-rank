#!/usr/bin/env python3
"""
Basic query tool for historical market cap data
"""
# /// script
# dependencies = [
#     "pandas",
#     "python-dateutil",
# ]
# ///

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

def load_jsonl(file_path: str) -> pd.DataFrame:
    """Load JSONL file into DataFrame"""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return pd.DataFrame(data)

def query_by_coin(df: pd.DataFrame, coin: str) -> pd.DataFrame:
    """Get all historical data for a specific coin"""
    result = df[df['coin'].str.lower() == coin.lower()]
    return result.sort_values('timestamp')

def query_by_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """Get all coins' data for a specific date"""
    df['date_only'] = pd.to_datetime(df['timestamp']).dt.date
    result = df[df['date_only'] == pd.to_datetime(target_date).date()]
    return result.sort_values('rank')

def query_top_n(df: pd.DataFrame, n: int = 10, date: Optional[str] = None) -> pd.DataFrame:
    """Get top N coins by market cap for a specific date or latest"""
    if date:
        df_filtered = query_by_date(df, date)
    else:
        latest_date = df['timestamp'].max()
        df_filtered = df[df['timestamp'] == latest_date]

    return df_filtered.nlargest(n, 'market_cap_usd')[['coin', 'symbol', 'price_usd', 'market_cap_usd', 'rank']]

def main():
    db_path = Path(__file__).parent / "market_cap_history.jsonl"

    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    print("Loading market cap data...")
    df = load_jsonl(str(db_path))
    print(f"Loaded {len(df)} records from {df['coin'].nunique()} unique coins")

    # Example queries
    print("\n=== Top 5 Coins by Market Cap (Latest) ===")
    top5 = query_top_n(df, n=5)
    print(top5.to_string(index=False))

    print("\n=== Bitcoin Historical Data ===")
    btc_data = query_by_coin(df, 'bitcoin')[['timestamp', 'price_usd', 'market_cap_usd', 'volume_24h']]
    print(btc_data.to_string(index=False))

    print("\n=== All Coins on 2025-11-15 ===")
    date_data = query_by_date(df, '2025-11-15')[['coin', 'symbol', 'price_usd', 'market_cap_usd', 'rank']]
    print(date_data.to_string(index=False))

if __name__ == "__main__":
    main()
