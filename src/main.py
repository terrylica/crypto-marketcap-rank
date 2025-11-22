#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "python-dateutil>=2.8.0",
#   "duckdb>=1.0.0",
#   "pyarrow>=15.0.0",
# ]
# ///
"""
Main Entry Point - Daily Cryptocurrency Rankings Collection

Orchestrates:
1. Data collection (CoinGecko API)
2. Database building (DuckDB + Parquet + CSV)
3. Validation (quality checks)

Adheres to SLO:
- Availability: Checkpoint-based resume
- Correctness: Validate each step, raise on errors
- Observability: Progress logging, metrics tracking
"""

import sys
from datetime import datetime

from builders.base_builder import BuildError
from builders.build_csv import CSVBuilder
from builders.build_duckdb import DuckDBBuilder
from builders.build_parquet import ParquetBuilder
from collectors.coingecko_collector import CoinGeckoCollector, CollectionError


def main(date: str = None):
    """
    Main pipeline: collect → build → validate.

    Args:
        date: Collection date (YYYY-MM-DD). Defaults to today.
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    print(f"{'='*80}")
    print("Crypto Market Cap Rankings - Daily Collection")
    print(f"{'='*80}")
    print(f"Date: {date}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    # Step 1: Collect data
    print("STEP 1: Data Collection")
    print("-" * 80)

    try:
        collector = CoinGeckoCollector()
        raw_file = collector.collect_all_coins(date=date)
        print(f"✅ Collection complete: {raw_file}\n")

    except CollectionError as e:
        print(f"❌ Collection failed: {e}")
        sys.exit(1)

    # Step 2: Build databases
    print("\nSTEP 2: Database Building")
    print("-" * 80)

    built_files = {}

    # Build DuckDB
    try:
        print("\n2a. Building DuckDB...")
        duckdb_builder = DuckDBBuilder()
        duckdb_file = duckdb_builder.build(raw_file)
        duckdb_builder.validate(duckdb_file)
        built_files['duckdb'] = duckdb_file
        print(f"✅ DuckDB complete: {duckdb_file}")

    except BuildError as e:
        print(f"❌ DuckDB build failed: {e}")
        sys.exit(1)

    # Build Parquet
    try:
        print("\n2b. Building Parquet...")
        parquet_builder = ParquetBuilder()
        parquet_dir = parquet_builder.build(raw_file)
        parquet_builder.validate(parquet_dir)
        built_files['parquet'] = parquet_dir
        print(f"✅ Parquet complete: {parquet_dir}")

    except BuildError as e:
        print(f"❌ Parquet build failed: {e}")
        sys.exit(1)

    # Build CSV
    try:
        print("\n2c. Building CSV...")
        csv_builder = CSVBuilder()
        csv_file = csv_builder.build(raw_file)
        csv_builder.validate(csv_file)
        built_files['csv'] = csv_file
        print(f"✅ CSV complete: {csv_file}")

    except BuildError as e:
        print(f"❌ CSV build failed: {e}")
        sys.exit(1)

    # Step 3: Summary
    print(f"\n{'='*80}")
    print("✅ Pipeline Complete!")
    print(f"{'='*80}")
    print(f"Date: {date}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nOutput files:")
    print(f"  Raw JSON:  {raw_file}")
    print(f"  DuckDB:    {built_files['duckdb']} ({built_files['duckdb'].stat().st_size / (1024*1024):.1f} MB)")
    print(f"  Parquet:   {built_files['parquet']}")
    print(f"  CSV:       {built_files['csv']} ({built_files['csv'].stat().st_size / (1024*1024):.1f} MB)")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Parse command-line arguments
    date = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        main(date=date)
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
