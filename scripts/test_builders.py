#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "duckdb>=1.0.0",
#   "pyarrow>=15.0.0",
# ]
# ///
"""
Test and validate all database builders.

This script:
1. Collects sample data (500 coins)
2. Builds DuckDB and Parquet formats
3. Validates each output
4. Reports file sizes and metrics

Usage:
    uv run scripts/test_builders.py
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from builders.build_duckdb import DuckDBBuilder
from builders.build_parquet import ParquetBuilder


def collect_sample_data() -> Path:
    """Collect sample data using tools/fetch_current_rankings.py logic."""
    import json
    import os
    import requests
    from datetime import datetime

    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.getenv('COINGECKO_API_KEY')
    top_n = 500
    per_page = 250
    pages = (top_n + per_page - 1) // per_page

    all_coins = []

    for page in range(1, pages + 1):
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

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        coins = response.json()
        all_coins.extend(coins)

        if page < pages:
            time.sleep(4 if api_key else 20)

    # Save in collector format
    date = datetime.now().strftime('%Y-%m-%d')
    data = {
        "metadata": {
            "collection_date": date,
            "total_coins": len(all_coins),
            "api_calls": pages,
            "collector_version": "test"
        },
        "coins": all_coins
    }

    output_file = output_dir / f"coingecko_rankings_{date}_test.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    return output_file


def main():
    """Run builder validation test."""
    print("=" * 80)
    print("Database Builders Validation Test")
    print("=" * 80)
    print()

    # Step 1: Collect sample data (500 coins for fast testing)
    print("Step 1: Collecting sample data (500 coins)...")
    print("-" * 80)

    try:
        raw_file = collect_sample_data()
        print(f"✅ Collection successful: {raw_file}")
        print()
    except Exception as e:
        print(f"❌ Collection failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 2: Build DuckDB
    print("Step 2: Building DuckDB database...")
    print("-" * 80)
    duckdb_builder = DuckDBBuilder(output_dir="data/processed")

    try:
        duckdb_file = duckdb_builder.build(raw_file)
        duckdb_builder.validate(duckdb_file)
        duckdb_size = duckdb_file.stat().st_size / (1024 * 1024)
        print(f"✅ DuckDB build successful: {duckdb_file} ({duckdb_size:.2f} MB)")
        print()
    except Exception as e:
        print(f"❌ DuckDB build failed: {e}")
        return 1

    # Step 3: Build Parquet
    print("Step 3: Building Parquet files...")
    print("-" * 80)
    parquet_builder = ParquetBuilder(output_dir="data/processed")

    try:
        parquet_dir = parquet_builder.build(raw_file)
        parquet_builder.validate(parquet_dir)
        parquet_size = sum(f.stat().st_size for f in parquet_dir.rglob("*.parquet")) / (1024 * 1024)
        print(f"✅ Parquet build successful: {parquet_dir} ({parquet_size:.2f} MB)")
        print()
    except Exception as e:
        print(f"❌ Parquet build failed: {e}")
        return 1

    # Summary
    print("=" * 80)
    print("✅ All builders validated successfully!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Raw JSON:  {raw_file.stat().st_size / (1024 * 1024):.2f} MB")
    print(f"  DuckDB:    {duckdb_size:.2f} MB")
    print(f"  Parquet:   {parquet_size:.2f} MB")
    print()
    print("Output files:")
    print(f"  {raw_file}")
    print(f"  {duckdb_file}")
    print(f"  {parquet_dir}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
