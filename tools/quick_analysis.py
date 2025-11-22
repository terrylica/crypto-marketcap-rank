#!/usr/bin/env python3
# /// script
# dependencies = ["pandas>=2.0.0"]
# ///
"""Quick analysis of crypto2 collected data."""

import sys
import pandas as pd

if len(sys.argv) < 2:
    print("Usage: uv run quick_analysis.py <csv_file>")
    sys.exit(1)

input_file = sys.argv[1]
print(f"\n{'='*70}")
print("crypto2 Collection Analysis - Quick Summary")
print(f"{'='*70}\n")
print(f"File: {input_file}")

df = pd.read_csv(input_file)
print(f"✅ Loaded {len(df):,} records\n")

print("Column Completeness:")
for col in ['timestamp', 'symbol', 'price', 'market_cap', 'circulating_supply', 'volume_24h']:
    if col in df.columns:
        non_null_pct = (df[col].notna().sum() / len(df)) * 100
        print(f"  {col:20s}: {non_null_pct:6.2f}% present")

print(f"\nData Summary:")
print(f"  Unique coins: {df['symbol'].nunique()}")
print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

# Top 10 coins by record count
print(f"\nTop 10 Coins by Record Count:")
top_coins = df['symbol'].value_counts().head(10)
for symbol, count in top_coins.items():
    print(f"  {symbol:10s}: {count:,} records")

# Bottom 10 coins by record count
print(f"\nBottom 10 Coins by Record Count:")
bottom_coins = df['symbol'].value_counts().tail(10)
for symbol, count in bottom_coins.items():
    print(f"  {symbol:10s}: {count:,} records")

# Check for circulating_supply presence
if 'circulating_supply' in df.columns:
    supply_pct = (df['circulating_supply'].notna().sum() / len(df)) * 100
    if supply_pct >= 95:
        print(f"\n✅ Excellent: {supply_pct:.1f}% of records have circulating_supply")
    elif supply_pct >= 75:
        print(f"\n⚠️  Good: {supply_pct:.1f}% of records have circulating_supply")
    else:
        print(f"\n⚠️  Warning: Only {supply_pct:.1f}% of records have circulating_supply")

# Check all collected coins
print(f"\n\nAll {df['symbol'].nunique()} Collected Coins:")
all_coins = sorted(df['symbol'].unique())
for i, coin in enumerate(all_coins, 1):
    coin_records = (df['symbol'] == coin).sum()
    print(f"  {i:2d}. {coin:10s} ({coin_records:,} records)")

print(f"\n{'='*70}\n")
