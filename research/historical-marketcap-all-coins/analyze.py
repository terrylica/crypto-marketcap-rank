#!/usr/bin/env python3
"""
Analysis tool for market cap growth rates and trends
"""
# /// script
# dependencies = [
#     "pandas",
#     "numpy",
# ]
# ///

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Tuple
import pandas as pd
import numpy as np

def load_jsonl(file_path: str) -> pd.DataFrame:
    """Load JSONL file into DataFrame"""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def calculate_growth_rate(start_value: float, end_value: float) -> float:
    """Calculate percentage growth rate"""
    if start_value == 0:
        return 0
    return ((end_value - start_value) / start_value) * 100

def coin_growth_analysis(df: pd.DataFrame, coin: str, days: int = 5) -> Dict:
    """Analyze growth rate for a specific coin over N days"""
    coin_data = df[df['coin'].str.lower() == coin.lower()].sort_values('timestamp')

    if len(coin_data) < 2:
        return {"coin": coin, "error": "Insufficient data"}

    latest = coin_data.iloc[-1]
    oldest = coin_data.iloc[0]

    market_cap_growth = calculate_growth_rate(oldest['market_cap_usd'], latest['market_cap_usd'])
    price_growth = calculate_growth_rate(oldest['price_usd'], latest['price_usd'])
    days_analyzed = (latest['timestamp'] - oldest['timestamp']).days

    return {
        "coin": coin,
        "symbol": latest['symbol'],
        "days_analyzed": days_analyzed,
        "start_date": oldest['timestamp'].strftime('%Y-%m-%d'),
        "end_date": latest['timestamp'].strftime('%Y-%m-%d'),
        "market_cap_growth_pct": round(market_cap_growth, 2),
        "price_growth_pct": round(price_growth, 2),
        "start_market_cap": oldest['market_cap_usd'],
        "end_market_cap": latest['market_cap_usd'],
        "start_price": oldest['price_usd'],
        "end_price": latest['price_usd'],
    }

def compare_coins(df: pd.DataFrame) -> pd.DataFrame:
    """Compare growth rates across all coins"""
    results = []
    for coin in df['coin'].unique():
        analysis = coin_growth_analysis(df, coin)
        if 'error' not in analysis:
            results.append(analysis)

    result_df = pd.DataFrame(results)
    return result_df.sort_values('market_cap_growth_pct', ascending=False)

def get_top_gainers(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Get top N gainers by market cap growth"""
    comparison = compare_coins(df)
    return comparison.head(n)[['coin', 'symbol', 'market_cap_growth_pct', 'price_growth_pct', 'start_market_cap', 'end_market_cap']]

def get_daily_rankings(df: pd.DataFrame) -> Dict:
    """Get how coin rankings changed over time"""
    df_sorted = df.sort_values('timestamp')
    dates = df_sorted['timestamp'].dt.date.unique()

    rankings = {}
    for date in dates:
        date_str = str(date)
        day_data = df_sorted[df_sorted['timestamp'].dt.date == date]
        top_coins = day_data.nlargest(5, 'market_cap_usd')[['coin', 'symbol', 'rank', 'market_cap_usd']]
        rankings[date_str] = top_coins.to_dict('records')

    return rankings

def calculate_volatility(df: pd.DataFrame, coin: str) -> Dict:
    """Calculate price volatility (standard deviation) for a coin"""
    coin_data = df[df['coin'].str.lower() == coin.lower()].sort_values('timestamp')

    if len(coin_data) < 2:
        return {"coin": coin, "error": "Insufficient data"}

    prices = coin_data['price_usd'].values
    returns = np.diff(prices) / prices[:-1] * 100  # Daily returns as percentage

    return {
        "coin": coin,
        "symbol": coin_data.iloc[-1]['symbol'],
        "num_data_points": len(coin_data),
        "price_std_dev": round(np.std(prices), 2),
        "daily_return_volatility_pct": round(np.std(returns), 2),
        "min_price": round(prices.min(), 2),
        "max_price": round(prices.max(), 2),
        "avg_price": round(prices.mean(), 2),
    }

def main():
    db_path = Path(__file__).parent / "market_cap_history.jsonl"

    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)

    print("Loading market cap data...")
    df = load_jsonl(str(db_path))
    print(f"Loaded {len(df)} records from {df['coin'].nunique()} unique coins\n")

    # Growth analysis
    print("=" * 70)
    print("MARKET CAP GROWTH ANALYSIS (Overall Period)")
    print("=" * 70)
    comparison = compare_coins(df)
    print(comparison[['coin', 'symbol', 'market_cap_growth_pct', 'price_growth_pct', 'days_analyzed']].to_string(index=False))

    print("\n" + "=" * 70)
    print("TOP 3 GAINERS")
    print("=" * 70)
    top_gainers = get_top_gainers(df, n=3)
    print(top_gainers.to_string(index=False))

    print("\n" + "=" * 70)
    print("PRICE VOLATILITY ANALYSIS")
    print("=" * 70)
    volatility_data = []
    for coin in df['coin'].unique():
        vol = calculate_volatility(df, coin)
        if 'error' not in vol:
            volatility_data.append(vol)

    vol_df = pd.DataFrame(volatility_data).sort_values('daily_return_volatility_pct', ascending=False)
    print(vol_df[['coin', 'symbol', 'daily_return_volatility_pct', 'min_price', 'max_price', 'avg_price']].to_string(index=False))

    print("\n" + "=" * 70)
    print("DAILY TOP 5 RANKINGS")
    print("=" * 70)
    rankings = get_daily_rankings(df)
    for date, coins in sorted(rankings.items()):
        print(f"\n{date}:")
        for coin_info in coins:
            print(f"  {coin_info['rank']}. {coin_info['coin'].upper()} ({coin_info['symbol']}) - "
                  f"${coin_info['market_cap_usd']:,.0f}")

if __name__ == "__main__":
    main()
