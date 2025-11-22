#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pandas>=2.0.0",
#   "numpy>=1.24.0",
#   "requests>=2.31.0",
# ]
# ///
"""
CoinGecko Free Tier Data Validation Script

ADR: 0001-hybrid-free-data-acquisition
Purpose: Validate CoinGecko 365-day historical data quality

Tests:
1. Date range coverage (365 days from present)
2. Field schema validation
3. Data completeness (no critical nulls/zeros)
4. Market cap consistency checks
5. Quality tier assessment (unverified flag)

Usage:
    uv run validation/scripts/validate_coingecko.py data/raw/coingecko/market_cap.csv

Exit Codes:
    0: All validations passed (with warnings about unverified data)
    1: Critical validation failed
"""

import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np


class CoinGeckoValidator:
    """Validates CoinGecko free tier historical data."""

    def __init__(self, csv_path: str):
        """
        Initialize validator.

        Args:
            csv_path: Path to CoinGecko CSV file

        Raises:
            FileNotFoundError: If CSV file doesn't exist
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"CoinGecko data file not found: {csv_path}\n"
                f"Expected location: data/raw/coingecko/market_cap.csv\n"
                f"NEXT STEP: Collect CoinGecko data using API or web scraping"
            )

        self.df = None
        self.validation_results = {}
        self.warnings = []

    def load_data(self) -> None:
        """
        Load and prepare data.

        Raises:
            ValueError: If CSV is empty or malformed
        """
        logger.info(f"Loading CoinGecko data from {self.csv_path}")

        try:
            self.df = pd.read_csv(self.csv_path)
        except Exception as e:
            raise ValueError(
                f"Failed to load CSV: {e}\n"
                f"File: {self.csv_path}\n"
                f"Ensure file is valid CSV format"
            )

        if len(self.df) == 0:
            raise ValueError(
                f"CoinGecko CSV is empty: {self.csv_path}\n"
                f"File exists but contains no data rows"
            )

        logger.info(f"Loaded {len(self.df):,} rows, {len(self.df.columns)} columns")
        logger.info(f"Columns: {list(self.df.columns)}")

    def test_schema(self) -> bool:
        """
        Validate schema has required fields.

        Required fields:
            - date (or timestamp)
            - symbol or id
            - name
            - price or current_price
            - market_cap or market_cap_usd
            - rank or market_cap_rank

        Returns:
            True if schema valid

        Raises:
            ValueError: If critical fields missing
        """
        logger.info("Test 1: Schema Validation")

        # Check for date field (various names)
        date_fields = ['date', 'timestamp', 'time', 'datetime']
        date_field = None
        for field in date_fields:
            if field in self.df.columns:
                date_field = field
                break

        if not date_field:
            raise ValueError(
                f"SCHEMA ERROR: No date field found\n"
                f"Expected one of: {date_fields}\n"
                f"Actual columns: {list(self.df.columns)}\n"
                f"CoinGecko data must include date/timestamp field"
            )

        logger.info(f"  ✅ Date field found: {date_field}")

        # Check for identifier (symbol or id)
        id_fields = ['symbol', 'id', 'coin_id', 'cryptocurrency']
        id_field = None
        for field in id_fields:
            if field in self.df.columns:
                id_field = field
                break

        if not id_field:
            raise ValueError(
                f"SCHEMA ERROR: No identifier field found\n"
                f"Expected one of: {id_fields}\n"
                f"Actual columns: {list(self.df.columns)}"
            )

        logger.info(f"  ✅ Identifier field found: {id_field}")

        # Check for price
        price_fields = ['price', 'current_price', 'price_usd', 'usd']
        price_field = None
        for field in price_fields:
            if field in self.df.columns:
                price_field = field
                break

        if not price_field:
            raise ValueError(
                f"SCHEMA ERROR: No price field found\n"
                f"Expected one of: {price_fields}\n"
                f"Actual columns: {list(self.df.columns)}"
            )

        logger.info(f"  ✅ Price field found: {price_field}")

        # Check for market cap
        mcap_fields = ['market_cap', 'market_cap_usd', 'mcap', 'marketcap']
        mcap_field = None
        for field in mcap_fields:
            if field in self.df.columns:
                mcap_field = field
                break

        if not mcap_field:
            raise ValueError(
                f"SCHEMA ERROR: No market_cap field found\n"
                f"Expected one of: {mcap_fields}\n"
                f"Actual columns: {list(self.df.columns)}"
            )

        logger.info(f"  ✅ Market cap field found: {mcap_field}")

        # Check for rank
        rank_fields = ['rank', 'market_cap_rank', 'cmc_rank', 'ranking']
        rank_field = None
        for field in rank_fields:
            if field in self.df.columns:
                rank_field = field
                break

        if not rank_field:
            self.warnings.append(
                "⚠️  No rank field found - will need to calculate from market cap"
            )
            logger.warning("  ⚠️  No rank field found")
        else:
            logger.info(f"  ✅ Rank field found: {rank_field}")

        # Check for circulating supply (expect missing)
        supply_fields = ['circulating_supply', 'supply', 'circulating']
        supply_field = None
        for field in supply_fields:
            if field in self.df.columns:
                supply_field = field
                break

        if supply_field:
            logger.info(f"  ✅ BONUS: Circulating supply field found: {supply_field}")
            self.warnings.append(
                f"✅ UNEXPECTED: Found circulating_supply field ({supply_field}) - "
                "can verify market cap calculation!"
            )
        else:
            logger.warning("  ⚠️  No circulating_supply field (expected for CoinGecko free tier)")
            self.warnings.append(
                "⚠️  QUALITY LIMITATION: No circulating_supply field in CoinGecko data\n"
                "   Cannot verify market_cap = price × supply calculation\n"
                "   Data will be flagged as 'unverified' quality tier"
            )

        # Store field mappings for later tests
        self.field_map = {
            'date': date_field,
            'id': id_field,
            'price': price_field,
            'market_cap': mcap_field,
            'rank': rank_field,
            'supply': supply_field
        }

        logger.info("  ✅ Schema validation PASSED")
        return True

    def test_date_coverage(self) -> bool:
        """
        Validate date range covers ~365 days.

        CoinGecko free tier should provide 365 days of history.

        Returns:
            True if coverage acceptable

        Raises:
            ValueError: If date range inadequate
        """
        logger.info("Test 2: Date Coverage Validation")

        date_field = self.field_map['date']

        # Convert to datetime
        try:
            self.df['parsed_date'] = pd.to_datetime(self.df[date_field])
        except Exception as e:
            raise ValueError(
                f"Failed to parse date field '{date_field}': {e}\n"
                f"Sample values: {self.df[date_field].head().tolist()}"
            )

        min_date = self.df['parsed_date'].min()
        max_date = self.df['parsed_date'].max()
        date_range_days = (max_date - min_date).days

        logger.info(f"  Date range: {min_date.date()} to {max_date.date()}")
        logger.info(f"  Coverage: {date_range_days} days")

        # Check if covers approximately 365 days
        if date_range_days < 300:
            raise ValueError(
                f"COVERAGE ERROR: Date range only {date_range_days} days\n"
                f"Expected: ~365 days for CoinGecko free tier\n"
                f"Range: {min_date.date()} to {max_date.date()}\n"
                f"RECOMMENDATION: Re-collect CoinGecko data or check API limits"
            )

        if date_range_days < 350:
            self.warnings.append(
                f"⚠️  Date coverage is {date_range_days} days (expected ~365)\n"
                f"   Slightly below expected range, but acceptable"
            )
            logger.warning(f"  ⚠️  Coverage {date_range_days} days (expected ~365)")

        # Check recency (max date should be recent)
        days_old = (datetime.now() - max_date).days
        if days_old > 7:
            self.warnings.append(
                f"⚠️  Data is {days_old} days old (last date: {max_date.date()})\n"
                f"   Consider refreshing CoinGecko data"
            )
            logger.warning(f"  ⚠️  Data {days_old} days old")

        logger.info("  ✅ Date coverage PASSED")
        return True

    def test_data_completeness(self) -> bool:
        """
        Check for nulls and zeros in critical fields.

        Returns:
            True if data complete

        Raises:
            ValueError: If critical data missing
        """
        logger.info("Test 3: Data Completeness Validation")

        critical_fields = ['price', 'market_cap']

        for field_key in critical_fields:
            field_name = self.field_map[field_key]
            if not field_name:
                continue

            # Check for nulls
            null_count = self.df[field_name].isnull().sum()
            null_pct = (null_count / len(self.df)) * 100

            if null_count > 0:
                logger.warning(
                    f"  ⚠️  {field_name}: {null_count:,} nulls ({null_pct:.2f}%)"
                )

                if null_pct > 5:
                    raise ValueError(
                        f"DATA QUALITY ERROR: {field_name} has {null_pct:.2f}% nulls\n"
                        f"Null count: {null_count:,} / {len(self.df):,} rows\n"
                        f"Maximum acceptable: 5%\n"
                        f"RECOMMENDATION: Re-collect CoinGecko data"
                    )

                self.warnings.append(
                    f"⚠️  {field_name} has {null_pct:.2f}% nulls (within tolerance)"
                )
            else:
                logger.info(f"  ✅ {field_name}: No nulls")

            # Check for zeros (prices/mcap should not be zero for ranked coins)
            zero_count = (self.df[field_name] == 0).sum()
            zero_pct = (zero_count / len(self.df)) * 100

            if zero_count > 0:
                logger.warning(
                    f"  ⚠️  {field_name}: {zero_count:,} zeros ({zero_pct:.2f}%)"
                )

                if zero_pct > 2:
                    raise ValueError(
                        f"DATA QUALITY ERROR: {field_name} has {zero_pct:.2f}% zeros\n"
                        f"Zero count: {zero_count:,} / {len(self.df):,} rows\n"
                        f"Prices and market caps should not be zero\n"
                        f"RECOMMENDATION: Investigate data collection issues"
                    )

                self.warnings.append(
                    f"⚠️  {field_name} has {zero_pct:.2f}% zeros (check if delisted coins)"
                )
            else:
                logger.info(f"  ✅ {field_name}: No zeros")

        logger.info("  ✅ Data completeness PASSED")
        return True

    def test_market_cap_consistency(self) -> bool:
        """
        Validate market cap values are reasonable.

        Checks:
        - Top coins have expected market cap ranges
        - Market cap ranks are consistent with values

        Returns:
            True if market cap data reasonable
        """
        logger.info("Test 4: Market Cap Consistency")

        mcap_field = self.field_map['market_cap']
        rank_field = self.field_map['rank']

        # Get most recent date
        latest_date = self.df['parsed_date'].max()
        latest_df = self.df[self.df['parsed_date'] == latest_date].copy()

        if rank_field:
            # Sort by rank
            latest_df = latest_df.sort_values(rank_field)
        else:
            # Sort by market cap
            latest_df = latest_df.sort_values(mcap_field, ascending=False)
            latest_df['calculated_rank'] = range(1, len(latest_df) + 1)

        # Check top 10 market caps
        top_10 = latest_df.head(10)
        logger.info(f"  Top 10 coins on {latest_date.date()}:")

        id_field = self.field_map['id']
        for idx, row in top_10.iterrows():
            coin_id = row[id_field]
            mcap = row[mcap_field]
            rank = row[rank_field] if rank_field else row['calculated_rank']

            logger.info(
                f"    #{int(rank):2d} {coin_id:10s} "
                f"Market Cap: ${mcap:,.0f}"
            )

        # Validate top coin has reasonable market cap (> $1B)
        top_mcap = top_10.iloc[0][mcap_field]
        if top_mcap < 1_000_000_000:
            self.warnings.append(
                f"⚠️  Top coin market cap is ${top_mcap:,.0f} (expected > $1B)\n"
                f"   Data may be incomplete or incorrect"
            )
            logger.warning(f"  ⚠️  Top market cap: ${top_mcap:,.0f} (expected > $1B)")
        else:
            logger.info(f"  ✅ Top market cap: ${top_mcap:,.0f}")

        # Check if rank ordering matches market cap ordering
        if rank_field:
            latest_df_sorted = latest_df.sort_values(mcap_field, ascending=False)
            latest_df_sorted['expected_rank'] = range(1, len(latest_df_sorted) + 1)

            rank_mismatches = (
                latest_df_sorted[rank_field] != latest_df_sorted['expected_rank']
            ).sum()

            if rank_mismatches > 0:
                mismatch_pct = (rank_mismatches / len(latest_df_sorted)) * 100
                self.warnings.append(
                    f"⚠️  Rank/MarketCap ordering mismatch: {rank_mismatches} coins ({mismatch_pct:.1f}%)\n"
                    f"   Provided rank may not match market cap sorting"
                )
                logger.warning(f"  ⚠️  Rank mismatches: {rank_mismatches}")
            else:
                logger.info("  ✅ Rank ordering matches market cap")

        logger.info("  ✅ Market cap consistency PASSED")
        return True

    def test_coin_coverage(self) -> bool:
        """
        Validate coverage of major coins.

        Checks if major cryptocurrencies are present.

        Returns:
            True if major coins present
        """
        logger.info("Test 5: Major Coin Coverage")

        id_field = self.field_map['id']

        # Get latest data
        latest_date = self.df['parsed_date'].max()
        latest_df = self.df[self.df['parsed_date'] == latest_date]

        # Major coins to check (various naming conventions)
        major_coins = {
            'BTC': ['btc', 'bitcoin', 'BTC', 'Bitcoin'],
            'ETH': ['eth', 'ethereum', 'ETH', 'Ethereum'],
            'USDT': ['usdt', 'tether', 'USDT', 'Tether'],
        }

        for symbol, variants in major_coins.items():
            found = False
            for variant in variants:
                if variant in latest_df[id_field].values:
                    found = True
                    logger.info(f"  ✅ {symbol} present (as '{variant}')")
                    break

            if not found:
                self.warnings.append(
                    f"⚠️  {symbol} not found in data (checked: {variants})\n"
                    f"   May affect ranking completeness"
                )
                logger.warning(f"  ⚠️  {symbol} not found")

        # Count unique coins
        unique_coins = latest_df[id_field].nunique()
        logger.info(f"  Total unique coins: {unique_coins}")

        if unique_coins < 100:
            self.warnings.append(
                f"⚠️  Only {unique_coins} unique coins found\n"
                f"   Expected: 100+ for top coin rankings"
            )
            logger.warning(f"  ⚠️  Low coin count: {unique_coins}")

        logger.info("  ✅ Coin coverage check COMPLETE")
        return True

    def generate_quality_assessment(self) -> Dict:
        """
        Generate quality tier assessment for CoinGecko data.

        Returns:
            Quality assessment dictionary
        """
        logger.info("Generating Quality Assessment")

        assessment = {
            'data_source': 'coingecko',
            'quality_tier': 'unverified',  # No circulating supply to verify mcap
            'date_range': {
                'min': self.df['parsed_date'].min().isoformat(),
                'max': self.df['parsed_date'].max().isoformat(),
                'days': (self.df['parsed_date'].max() - self.df['parsed_date'].min()).days
            },
            'record_count': len(self.df),
            'unique_coins': self.df[self.field_map['id']].nunique(),
            'has_circulating_supply': self.field_map['supply'] is not None,
            'limitations': [
                'Market cap is pre-calculated by CoinGecko (cannot verify calculation)',
                'No historical circulating supply data',
                'Limited to 365 days (free tier restriction)',
                'Data flagged as unverified quality tier'
            ],
            'recommended_use': '2024-2025 recent period only',
            'warnings': self.warnings
        }

        logger.info(f"  Quality Tier: {assessment['quality_tier']}")
        logger.info(f"  Coverage: {assessment['date_range']['days']} days")
        logger.info(f"  Records: {assessment['record_count']:,}")
        logger.info(f"  Unique Coins: {assessment['unique_coins']}")

        return assessment

    def run_all_tests(self) -> bool:
        """
        Run complete validation suite.

        Returns:
            True if all tests passed (with warnings acceptable)

        Raises:
            ValueError: If any critical test fails
        """
        logger.info("="*60)
        logger.info("CoinGecko Data Validation Suite")
        logger.info("="*60)

        self.load_data()

        tests = [
            self.test_schema,
            self.test_date_coverage,
            self.test_data_completeness,
            self.test_market_cap_consistency,
            self.test_coin_coverage,
        ]

        for test in tests:
            test()
            logger.info("")

        assessment = self.generate_quality_assessment()

        logger.info("="*60)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*60)

        if self.warnings:
            logger.info(f"⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.info(f"  {warning}")
            logger.info("")

        logger.info("✅ All validation tests PASSED")
        logger.info("")
        logger.info("QUALITY TIER: UNVERIFIED")
        logger.info("  - CoinGecko data is usable but flagged as unverified")
        logger.info("  - Cannot verify market_cap calculation (no circulating_supply)")
        logger.info("  - Recommended for 2024-2025 period only")
        logger.info("  - Will be merged with verified data (Kaggle + crypto2)")
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("  1. Use this data for 2024-2025 recent period")
        logger.info("  2. Combine with verified data from Kaggle/crypto2")
        logger.info("  3. Flag all CoinGecko records as quality_tier='unverified'")
        logger.info("  4. Document limitations in final dataset README")

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
        description='Validate CoinGecko historical data quality'
    )
    parser.add_argument(
        'csv_path',
        help='Path to CoinGecko CSV file (e.g., data/raw/coingecko/market_cap.csv)'
    )
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Directory for log files (default: logs/)'
    )

    args = parser.parse_args()

    # Setup logging
    log_dir = Path(args.log_dir)
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'0001-coingecko-validation-{timestamp}.log'

    setup_logging(log_file)

    global logger
    logger = logging.getLogger(__name__)

    logger.info(f"CoinGecko Validation Log: {log_file}")
    logger.info(f"Input file: {args.csv_path}")
    logger.info("")

    try:
        validator = CoinGeckoValidator(args.csv_path)
        validator.run_all_tests()

        logger.info(f"Log saved to: {log_file}")
        return 0

    except Exception as e:
        logger.error("="*60)
        logger.error("VALIDATION FAILED")
        logger.error("="*60)
        logger.error(f"Error: {e}")
        logger.error("")
        logger.error(f"Full log: {log_file}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
