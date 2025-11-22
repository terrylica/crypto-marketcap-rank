#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pandas>=2.0.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Data Merge Pipeline

ADR: 0001-hybrid-free-data-acquisition
Purpose: Merge Kaggle + crypto2 + CoinGecko datasets with quality tier flagging

Strategy:
1. Load all available datasets
2. Standardize schemas (column names, data types)
3. Add data_source and quality_tier columns
4. Merge with priority: Kaggle (verified) > crypto2 (verified) > CoinGecko (unverified)
5. Remove duplicate (date, symbol) combinations
6. Sort by date and rank
7. Save final dataset with metadata

Quality Tiers:
- verified: Has circulating_supply field to verify market_cap = price × supply
- unverified: Pre-calculated market_cap without circulating_supply

Usage:
    uv run tools/merge_datasets.py \\
        --kaggle data/raw/kaggle/historical_data.csv \\
        --crypto2 data/raw/crypto2/scenario_a_gap_*.csv \\
        --coingecko data/raw/coingecko/market_cap.csv \\
        --output data/final/crypto_historical_marketcap_ranked.csv

Exit Codes:
    0: Merge successful
    1: Error during merge
"""

import sys
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import numpy as np


class DatasetMerger:
    """Merges cryptocurrency datasets from multiple sources."""

    # Standard column schema
    STANDARD_SCHEMA = {
        'date': 'date',
        'symbol': 'symbol',
        'name': 'name',
        'price_usd': 'price_usd',
        'volume_24h': 'volume_24h',
        'market_cap_usd': 'market_cap_usd',
        'circulating_supply': 'circulating_supply',
        'rank': 'rank',
        'data_source': 'data_source',
        'quality_tier': 'quality_tier'
    }

    def __init__(self, output_dir: str = 'data/final'):
        """Initialize merger."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.datasets = []
        self.merged_df = None
        self.metadata = {
            'merge_date': datetime.now().isoformat(),
            'sources': {},
            'quality_summary': {},
            'warnings': []
        }

    def load_kaggle(self, csv_path: Optional[str]) -> Optional[pd.DataFrame]:
        """
        Load and standardize Kaggle dataset.

        Args:
            csv_path: Path to Kaggle CSV (optional)

        Returns:
            Standardized dataframe or None
        """
        if not csv_path or csv_path == 'none':
            logger.info("Kaggle dataset: Not provided (skipping)")
            return None

        csv_path = Path(csv_path)
        if not csv_path.exists():
            logger.warning(f"Kaggle dataset not found: {csv_path} (skipping)")
            return None

        logger.info(f"Loading Kaggle dataset from {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            logger.info(f"  Loaded {len(df):,} rows")

            # Standardize column names (Kaggle specific mapping)
            column_mapping = {
                'Date': 'date',
                'Symbol': 'symbol',
                'Name': 'name',
                'Close': 'price_usd',
                'Volume': 'volume_24h',
                'Market Cap': 'market_cap_usd',
                'Rank': 'rank',
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Add data source and quality tier
            df['data_source'] = 'kaggle'
            df['quality_tier'] = 'verified'  # Kaggle has historical snapshots

            # Ensure required columns exist
            for col in ['date', 'symbol', 'price_usd', 'market_cap_usd']:
                if col not in df.columns:
                    raise ValueError(f"Missing required column after mapping: {col}")

            # Add circulating_supply if missing (calculate from price and mcap)
            if 'circulating_supply' not in df.columns:
                df['circulating_supply'] = df['market_cap_usd'] / df['price_usd']
                logger.info("  Calculated circulating_supply from market_cap / price")

            logger.info(f"  ✅ Kaggle dataset standardized")

            self.metadata['sources']['kaggle'] = {
                'file': str(csv_path),
                'records': len(df),
                'date_range': (df['date'].min(), df['date'].max()),
                'unique_coins': df['symbol'].nunique()
            }

            return df

        except Exception as e:
            logger.error(f"Failed to load Kaggle dataset: {e}")
            self.metadata['warnings'].append(f"Kaggle load failed: {e}")
            return None

    def load_crypto2(self, csv_path: Optional[str]) -> Optional[pd.DataFrame]:
        """
        Load and standardize crypto2 dataset.

        Args:
            csv_path: Path to crypto2 CSV (supports wildcards)

        Returns:
            Standardized dataframe or None
        """
        if not csv_path or csv_path == 'none':
            logger.info("crypto2 dataset: Not provided (skipping)")
            return None

        # Handle wildcard paths
        csv_files = list(Path('.').glob(csv_path))

        if len(csv_files) == 0:
            logger.warning(f"crypto2 dataset not found: {csv_path} (skipping)")
            return None

        if len(csv_files) > 1:
            logger.info(f"Found {len(csv_files)} crypto2 files, using most recent")
            csv_files = sorted(csv_files, key=lambda p: p.stat().st_mtime, reverse=True)

        csv_path = csv_files[0]
        logger.info(f"Loading crypto2 dataset from {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            logger.info(f"  Loaded {len(df):,} rows")

            # Standardize column names (crypto2 specific mapping)
            column_mapping = {
                'timestamp': 'date',
                'coin_symbol': 'symbol',
                'coin_name': 'name',
                'price': 'price_usd',
                'volume_24h': 'volume_24h',
                'market_cap': 'market_cap_usd',
                'circulating_supply': 'circulating_supply',
                'cmc_rank': 'rank',
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Add data source and quality tier
            df['data_source'] = 'crypto2'
            df['quality_tier'] = 'verified'  # crypto2 has circulating_supply

            # Ensure required columns exist
            for col in ['date', 'symbol', 'price_usd', 'market_cap_usd']:
                if col not in df.columns:
                    raise ValueError(f"Missing required column after mapping: {col}")

            # Verify circulating_supply exists
            if 'circulating_supply' not in df.columns:
                logger.warning("  ⚠️  crypto2 missing circulating_supply - marking as unverified")
                df['circulating_supply'] = np.nan
                df['quality_tier'] = 'unverified'

            logger.info(f"  ✅ crypto2 dataset standardized")

            self.metadata['sources']['crypto2'] = {
                'file': str(csv_path),
                'records': len(df),
                'date_range': (df['date'].min(), df['date'].max()),
                'unique_coins': df['symbol'].nunique()
            }

            return df

        except Exception as e:
            logger.error(f"Failed to load crypto2 dataset: {e}")
            self.metadata['warnings'].append(f"crypto2 load failed: {e}")
            return None

    def load_coingecko(self, csv_path: Optional[str]) -> Optional[pd.DataFrame]:
        """
        Load and standardize CoinGecko dataset.

        Args:
            csv_path: Path to CoinGecko CSV

        Returns:
            Standardized dataframe or None
        """
        if not csv_path or csv_path == 'none':
            logger.info("CoinGecko dataset: Not provided (skipping)")
            return None

        csv_path = Path(csv_path)
        if not csv_path.exists():
            logger.warning(f"CoinGecko dataset not found: {csv_path} (skipping)")
            return None

        logger.info(f"Loading CoinGecko dataset from {csv_path}")

        try:
            df = pd.read_csv(csv_path)
            logger.info(f"  Loaded {len(df):,} rows")

            # Standardize column names (CoinGecko specific mapping)
            column_mapping = {
                'date': 'date',
                'id': 'symbol',  # CoinGecko uses 'id' not symbol
                'name': 'name',
                'current_price': 'price_usd',
                'total_volume': 'volume_24h',
                'market_cap': 'market_cap_usd',
                'market_cap_rank': 'rank',
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Add data source and quality tier
            df['data_source'] = 'coingecko'
            df['quality_tier'] = 'unverified'  # CoinGecko free tier has no circulating_supply

            # Ensure required columns exist
            for col in ['date', 'symbol', 'price_usd', 'market_cap_usd']:
                if col not in df.columns:
                    raise ValueError(f"Missing required column after mapping: {col}")

            # Add empty circulating_supply column
            if 'circulating_supply' not in df.columns:
                df['circulating_supply'] = np.nan

            logger.info(f"  ✅ CoinGecko dataset standardized")
            logger.info(f"  ⚠️  Quality tier: unverified (no circulating_supply)")

            self.metadata['sources']['coingecko'] = {
                'file': str(csv_path),
                'records': len(df),
                'date_range': (df['date'].min(), df['date'].max()),
                'unique_coins': df['symbol'].nunique()
            }

            return None

        except Exception as e:
            logger.error(f"Failed to load CoinGecko dataset: {e}")
            self.metadata['warnings'].append(f"CoinGecko load failed: {e}")
            return None

    def merge_datasets(self) -> pd.DataFrame:
        """
        Merge all loaded datasets.

        Priority: Kaggle > crypto2 > CoinGecko (verified > unverified)

        Returns:
            Merged dataframe
        """
        logger.info("="*60)
        logger.info("Merging Datasets")
        logger.info("="*60)

        if len(self.datasets) == 0:
            raise ValueError("No datasets loaded - nothing to merge")

        # Concatenate all datasets
        logger.info(f"Concatenating {len(self.datasets)} datasets...")
        combined = pd.concat(self.datasets, ignore_index=True)

        logger.info(f"  Total records before deduplication: {len(combined):,}")

        # Convert date to datetime for comparison
        combined['date_parsed'] = pd.to_datetime(combined['date'])

        # Normalize symbols (uppercase)
        combined['symbol_normalized'] = combined['symbol'].str.upper()

        # Sort by priority: quality_tier (verified first), then data_source
        source_priority = {'kaggle': 1, 'crypto2': 2, 'coingecko': 3}
        tier_priority = {'verified': 1, 'unverified': 2}

        combined['source_priority'] = combined['data_source'].map(source_priority)
        combined['tier_priority'] = combined['quality_tier'].map(tier_priority)

        combined = combined.sort_values(
            ['tier_priority', 'source_priority', 'date_parsed', 'symbol_normalized']
        )

        # Remove duplicates: keep first (highest priority) for each (date, symbol)
        logger.info("  Removing duplicates (date, symbol) - keeping highest priority source...")

        before_dedup = len(combined)
        combined = combined.drop_duplicates(
            subset=['date_parsed', 'symbol_normalized'],
            keep='first'
        )
        after_dedup = len(combined)

        duplicates_removed = before_dedup - after_dedup
        logger.info(f"  Removed {duplicates_removed:,} duplicate records")

        # Drop helper columns
        combined = combined.drop(columns=[
            'date_parsed', 'symbol_normalized', 'source_priority', 'tier_priority'
        ])

        # Sort by date and rank
        combined = combined.sort_values(['date', 'rank'])

        logger.info(f"  ✅ Final merged dataset: {len(combined):,} records")

        self.merged_df = combined
        return combined

    def generate_metadata(self) -> Dict:
        """
        Generate metadata file describing the merged dataset.

        Returns:
            Metadata dictionary
        """
        if self.merged_df is None:
            raise ValueError("No merged dataset to generate metadata from")

        logger.info("Generating metadata...")

        # Quality tier distribution
        quality_dist = self.merged_df['quality_tier'].value_counts().to_dict()
        source_dist = self.merged_df['data_source'].value_counts().to_dict()

        self.metadata['quality_summary'] = {
            'total_records': len(self.merged_df),
            'quality_distribution': quality_dist,
            'source_distribution': source_dist,
            'date_range': {
                'min': self.merged_df['date'].min(),
                'max': self.merged_df['date'].max()
            },
            'unique_coins': self.merged_df['symbol'].nunique(),
            'verified_percentage': (
                quality_dist.get('verified', 0) / len(self.merged_df)
            ) * 100
        }

        logger.info(f"  Total records: {self.metadata['quality_summary']['total_records']:,}")
        logger.info(f"  Verified: {quality_dist.get('verified', 0):,} "
                   f"({self.metadata['quality_summary']['verified_percentage']:.1f}%)")
        logger.info(f"  Unverified: {quality_dist.get('unverified', 0):,}")

        return self.metadata

    def save_output(self, output_path: Path) -> None:
        """
        Save merged dataset and metadata.

        Args:
            output_path: Path for output CSV
        """
        if self.merged_df is None:
            raise ValueError("No merged dataset to save")

        logger.info("="*60)
        logger.info("Saving Output")
        logger.info("="*60)

        # Save main CSV
        logger.info(f"Saving merged dataset to {output_path}")
        self.merged_df.to_csv(output_path, index=False)

        file_size_mb = output_path.stat().st_size / 1024 / 1024
        logger.info(f"  ✅ Saved {len(self.merged_df):,} records ({file_size_mb:.1f} MB)")

        # Save compressed version
        output_gz = output_path.with_suffix('.csv.gz')
        logger.info(f"Saving compressed version to {output_gz}")
        self.merged_df.to_csv(output_gz, index=False, compression='gzip')

        gz_size_mb = output_gz.stat().st_size / 1024 / 1024
        compression_ratio = (1 - gz_size_mb / file_size_mb) * 100
        logger.info(f"  ✅ Saved compressed ({gz_size_mb:.1f} MB, {compression_ratio:.0f}% smaller)")

        # Save metadata
        metadata_path = output_path.with_suffix('.json')
        logger.info(f"Saving metadata to {metadata_path}")

        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"  ✅ Metadata saved")

    def run(self, kaggle_path: Optional[str], crypto2_path: Optional[str],
            coingecko_path: Optional[str], output_path: str) -> bool:
        """
        Run complete merge pipeline.

        Args:
            kaggle_path: Path to Kaggle CSV (or 'none')
            crypto2_path: Path to crypto2 CSV (or 'none')
            coingecko_path: Path to CoinGecko CSV (or 'none')
            output_path: Output path for merged CSV

        Returns:
            True if successful
        """
        logger.info("="*70)
        logger.info("DATA MERGE PIPELINE")
        logger.info("="*70)
        logger.info("")

        # Load datasets
        kaggle_df = self.load_kaggle(kaggle_path)
        if kaggle_df is not None:
            self.datasets.append(kaggle_df)

        crypto2_df = self.load_crypto2(crypto2_path)
        if crypto2_df is not None:
            self.datasets.append(crypto2_df)

        coingecko_df = self.load_coingecko(coingecko_path)
        if coingecko_df is not None:
            self.datasets.append(coingecko_df)

        if len(self.datasets) == 0:
            raise ValueError(
                "No datasets could be loaded\n"
                "At least one dataset (Kaggle, crypto2, or CoinGecko) is required"
            )

        logger.info("")

        # Merge
        self.merge_datasets()

        logger.info("")

        # Generate metadata
        self.generate_metadata()

        logger.info("")

        # Save output
        output_path = Path(output_path)
        self.save_output(output_path)

        logger.info("")
        logger.info("="*70)
        logger.info("MERGE COMPLETE")
        logger.info("="*70)
        logger.info(f"Output: {output_path}")
        logger.info(f"Compressed: {output_path.with_suffix('.csv.gz')}")
        logger.info(f"Metadata: {output_path.with_suffix('.json')}")
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("  1. Run bias prevention validation:")
        logger.info(f"     uv run validation/scripts/validate_bias_prevention.py {output_path}")
        logger.info("  2. Review metadata file for quality distribution")
        logger.info("  3. Generate final validation report")

        return True


def setup_logging(log_file: Path) -> None:
    """Setup logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Merge Kaggle + crypto2 + CoinGecko datasets'
    )
    parser.add_argument(
        '--kaggle',
        default='none',
        help='Path to Kaggle CSV (or "none" to skip)'
    )
    parser.add_argument(
        '--crypto2',
        default='none',
        help='Path to crypto2 CSV (supports wildcards, or "none" to skip)'
    )
    parser.add_argument(
        '--coingecko',
        default='none',
        help='Path to CoinGecko CSV (or "none" to skip)'
    )
    parser.add_argument(
        '--output',
        default='data/final/crypto_historical_marketcap_ranked.csv',
        help='Output path for merged CSV'
    )
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Directory for log files'
    )

    args = parser.parse_args()

    # Setup logging
    log_dir = Path(args.log_dir)
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'0001-merge-datasets-{timestamp}.log'

    setup_logging(log_file)

    global logger
    logger = logging.getLogger(__name__)

    logger.info(f"Merge Pipeline Log: {log_file}")
    logger.info("")

    try:
        merger = DatasetMerger()
        merger.run(
            kaggle_path=args.kaggle,
            crypto2_path=args.crypto2,
            coingecko_path=args.coingecko,
            output_path=args.output
        )

        logger.info(f"Log saved to: {log_file}")
        return 0

    except Exception as e:
        logger.error("="*70)
        logger.error("MERGE FAILED")
        logger.error("="*70)
        logger.error(f"Error: {e}")
        logger.error("")
        logger.error(f"Full log: {log_file}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
