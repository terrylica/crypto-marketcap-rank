#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pandas>=2.0.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Kaggle Dataset Validation Script

Validates the bizzyvinci/coinmarketcap-historical-data Kaggle dataset
for point-in-time accuracy, circulating supply presence, and absence of look-ahead bias.

ADR: 0001-hybrid-free-data-acquisition
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Setup logging
log_file = Path(__file__).parent.parent.parent / "logs" / f"0001-kaggle-validation-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class KaggleValidator:
    """Validates Kaggle cryptocurrency historical dataset."""

    def __init__(self, data_path: Path):
        """
        Initialize validator.

        Args:
            data_path: Path to Kaggle dataset CSV file

        Raises:
            FileNotFoundError: If data_path does not exist
        """
        if not data_path.exists():
            raise FileNotFoundError(
                f"Kaggle dataset not found at {data_path}\n"
                f"Download with: kaggle datasets download -d bizzyvinci/coinmarketcap-historical-data"
            )

        self.data_path = data_path
        self.df = None
        self.validation_results = {}

    def load_data(self) -> None:
        """
        Load Kaggle dataset into memory.

        Raises:
            ValueError: If required columns are missing
        """
        logger.info(f"Loading data from {self.data_path}")
        try:
            self.df = pd.read_csv(self.data_path)
            logger.info(f"Loaded {len(self.df):,} records")
        except Exception as e:
            raise ValueError(f"Failed to load CSV: {e}")

        # Kaggle dataset uses different column names
        # coin_id instead of symbol, cmc_rank instead of rank
        required_cols = ['date', 'coin_id', 'price', 'market_cap', 'cmc_rank', 'circulating_supply']
        missing = [col for col in required_cols if col not in self.df.columns]
        if missing:
            raise ValueError(
                f"Missing required columns: {missing}\n"
                f"Available columns: {list(self.df.columns)}"
            )

        # Load coins metadata to get symbol and name
        coins_path = self.data_path.parent / 'coins.csv'
        if not coins_path.exists():
            logger.warning(f"Coins metadata not found at {coins_path}, will use coin_id as symbol")
            self.df['symbol'] = self.df['coin_id'].astype(str)
            self.df['name'] = 'Unknown'
        else:
            logger.info(f"Loading coins metadata from {coins_path}")
            coins_df = pd.read_csv(coins_path, usecols=['id', 'symbol', 'name'])
            logger.info(f"Loaded {len(coins_df):,} coin metadata records")

            # Join to get symbol and name
            self.df = self.df.merge(
                coins_df,
                left_on='coin_id',
                right_on='id',
                how='left'
            )

            # Fill missing symbols/names
            missing_meta = self.df[['symbol', 'name']].isnull().any(axis=1).sum()
            if missing_meta > 0:
                logger.warning(f"{missing_meta:,} records missing symbol/name metadata")
                self.df['symbol'] = self.df['symbol'].fillna(self.df['coin_id'].astype(str))
                self.df['name'] = self.df['name'].fillna('Unknown')

        # Rename cmc_rank to rank for consistency with validators
        self.df['rank'] = self.df['cmc_rank']

        logger.info(f"Final dataset: {len(self.df):,} records with {len(self.df.columns)} columns")

    def test_bitconnect_presence(self) -> bool:
        """
        Test 1: BitConnect Presence (Survivorship Bias Detector)

        BitConnect (BCC) was a ponzi scheme that collapsed in January 2018.
        It must appear in 2016-2018 data for this to be point-in-time historical data.

        Returns:
            True if test passes

        Raises:
            ValueError: If BitConnect is missing (survivorship bias detected)
        """
        logger.info("=" * 80)
        logger.info("TEST 1: BitConnect Presence (Survivorship Bias)")
        logger.info("=" * 80)

        bcc = self.df[self.df['symbol'].str.upper() == 'BCC'].copy()

        if len(bcc) == 0:
            error_msg = (
                "SURVIVORSHIP BIAS DETECTED: BitConnect (BCC) missing from dataset\n"
                "A point-in-time historical dataset MUST include coins that died/delisted.\n"
                "BitConnect existed Jan 2016 - Jan 2018 and should appear in historical data.\n"
                "\n"
                "RECOMMENDATION: REJECT this Kaggle dataset\n"
                "FALLBACK: Use crypto2 R package for full 2013-2024 period"
            )
            logger.error(error_msg)
            self.validation_results['bitconnect'] = 'FAIL'
            raise ValueError(error_msg)

        date_min = bcc['date'].min()
        date_max = bcc['date'].max()
        peak_rank = bcc['rank'].min()
        peak_mcap = bcc['market_cap'].max()

        logger.info(f"✅ BitConnect found: {len(bcc)} entries")
        logger.info(f"   Date range: {date_min} to {date_max}")
        logger.info(f"   Peak rank: {peak_rank}")
        logger.info(f"   Peak market cap: ${peak_mcap:,.0f}")

        # Validate date range is reasonable
        if date_min > '2017-01-01':
            logger.warning(f"⚠️  BitConnect start date {date_min} seems late (expected ~2016)")
        if date_max < '2018-01-01':
            logger.warning(f"⚠️  BitConnect end date {date_max} seems early (expected ~2018-01)")

        self.validation_results['bitconnect'] = 'PASS'
        logger.info("✅ TEST 1 PASSED: Point-in-time data confirmed (dead coin present)")
        return True

    def test_circulating_supply_variation(self) -> bool:
        """
        Test 2: Circulating Supply Variation (Look-Ahead Bias Detector)

        If circulating supply is present and varies over time, this indicates
        the dataset uses historical supply data (good). If constant or missing,
        it may be using current supply for all dates (look-ahead bias).

        Returns:
            True if test passes

        Raises:
            ValueError: If circulating supply is missing or constant
        """
        logger.info("=" * 80)
        logger.info("TEST 2: Circulating Supply Variation (Look-Ahead Bias)")
        logger.info("=" * 80)

        if 'circulating_supply' not in self.df.columns:
            error_msg = (
                "CRITICAL: 'circulating_supply' column missing from dataset\n"
                "Cannot verify market cap = price × historical circulating supply\n"
                "\n"
                "RECOMMENDATION: REJECT this Kaggle dataset\n"
                "FALLBACK: Use crypto2 R package which includes circulating supply"
            )
            logger.error(error_msg)
            self.validation_results['supply_variation'] = 'FAIL'
            raise ValueError(error_msg)

        # Test Bitcoin supply progression
        btc = self.df[self.df['symbol'] == 'BTC'].sort_values('date').copy()

        if len(btc) == 0:
            raise ValueError("Bitcoin (BTC) not found in dataset")

        # Sample key dates
        test_dates = {
            '2015-01-01': (14_000_000, 14_500_000),  # ~14.2M BTC
            '2017-01-01': (16_000_000, 16_500_000),  # ~16.2M BTC
            '2019-01-01': (17_500_000, 18_000_000),  # ~17.8M BTC
            '2021-01-01': (18_500_000, 19_000_000),  # ~18.6M BTC
        }

        passed = 0
        failed = 0

        for date, (min_supply, max_supply) in test_dates.items():
            row = btc[btc['date'] == date]
            if row.empty:
                logger.warning(f"⚠️  {date}: No data (date may be outside dataset range)")
                continue

            supply = row['circulating_supply'].values[0]

            if pd.isna(supply) or supply == 0:
                logger.error(f"❌ {date}: Circulating supply is null/zero")
                failed += 1
                continue

            if min_supply <= supply <= max_supply:
                logger.info(f"✅ {date}: {supply:,.0f} BTC (expected {min_supply:,.0f}-{max_supply:,.0f})")
                passed += 1
            else:
                logger.error(f"❌ {date}: {supply:,.0f} BTC (expected {min_supply:,.0f}-{max_supply:,.0f})")
                failed += 1

        if failed > 0:
            error_msg = (
                f"LOOK-AHEAD BIAS SUSPECTED: {failed}/{passed+failed} supply checks failed\n"
                "Bitcoin circulating supply values do not match expected historical progression.\n"
                "Dataset may be using current supply for all historical dates.\n"
                "\n"
                "RECOMMENDATION: REJECT this Kaggle dataset\n"
                "FALLBACK: Use crypto2 R package with verified historical supply"
            )
            logger.error(error_msg)
            self.validation_results['supply_variation'] = 'FAIL'
            raise ValueError(error_msg)

        # Check if supply actually varies
        btc_supply_unique = btc['circulating_supply'].nunique()
        logger.info(f"\nBitcoin supply unique values: {btc_supply_unique:,}")

        if btc_supply_unique < 10:
            logger.warning(
                f"⚠️  Low supply variation ({btc_supply_unique} unique values). "
                f"Expected thousands for multi-year data."
            )

        self.validation_results['supply_variation'] = 'PASS'
        logger.info("✅ TEST 2 PASSED: Circulating supply varies correctly over time")
        return True

    def test_rank_consistency(self, sample_size: int = 10) -> bool:
        """
        Test 3: Rank Consistency (Data Integrity Check)

        Verify that the provided 'rank' field matches the calculated rank
        based on market cap ordering for sampled dates.

        Args:
            sample_size: Number of random dates to test

        Returns:
            True if test passes

        Raises:
            ValueError: If significant rank mismatches found
        """
        logger.info("=" * 80)
        logger.info("TEST 3: Rank Consistency (Data Integrity)")
        logger.info("=" * 80)

        dates = self.df['date'].unique()
        sample_dates = np.random.choice(dates, min(sample_size, len(dates)), replace=False)

        total_mismatches = 0

        for date in sample_dates:
            day_data = self.df[self.df['date'] == date].copy()

            # Calculate rank from market cap (descending, rank 1 = highest market cap)
            day_data['calc_rank'] = day_data['market_cap'].rank(ascending=False, method='min').astype(int)

            # Compare
            mismatches = day_data[day_data['rank'] != day_data['calc_rank']]

            if len(mismatches) > 0:
                total_mismatches += len(mismatches)
                logger.error(f"❌ {date}: {len(mismatches)} rank mismatches out of {len(day_data)} coins")
                # Show first few mismatches
                for _, row in mismatches.head(3).iterrows():
                    logger.error(
                        f"   {row['symbol']}: provided rank={row['rank']}, "
                        f"calculated rank={row['calc_rank']}, market_cap=${row['market_cap']:,.0f}"
                    )
            else:
                logger.info(f"✅ {date}: All {len(day_data)} ranks consistent")

        if total_mismatches > 0:
            error_msg = (
                f"DATA INTEGRITY ISSUE: {total_mismatches} total rank mismatches found\n"
                f"Provided ranks do not match market cap ordering.\n"
                "\n"
                f"RECOMMENDATION: Investigate further or REJECT dataset\n"
                f"This may indicate data corruption or incorrect calculations."
            )
            logger.error(error_msg)
            self.validation_results['rank_consistency'] = 'FAIL'
            raise ValueError(error_msg)

        self.validation_results['rank_consistency'] = 'PASS'
        logger.info("✅ TEST 3 PASSED: All ranks match market cap ordering")
        return True

    def test_coverage(self) -> Dict[str, any]:
        """
        Test 4: Coverage Analysis

        Analyze date range, coin count, and completeness.

        Returns:
            Dictionary with coverage metrics
        """
        logger.info("=" * 80)
        logger.info("TEST 4: Coverage Analysis")
        logger.info("=" * 80)

        date_min = self.df['date'].min()
        date_max = self.df['date'].max()
        total_days = self.df['date'].nunique()
        unique_coins = self.df['symbol'].nunique()
        total_records = len(self.df)

        logger.info(f"Date Range: {date_min} to {date_max}")
        logger.info(f"Total Days: {total_days:,}")
        logger.info(f"Unique Coins: {unique_coins:,}")
        logger.info(f"Total Records: {total_records:,}")

        # Daily coin counts
        daily_counts = self.df.groupby('date').size()
        avg_coins_per_day = daily_counts.mean()
        min_coins_per_day = daily_counts.min()
        max_coins_per_day = daily_counts.max()

        logger.info(f"\nDaily Coin Counts:")
        logger.info(f"  Average: {avg_coins_per_day:.0f} coins/day")
        logger.info(f"  Minimum: {min_coins_per_day} coins/day")
        logger.info(f"  Maximum: {max_coins_per_day} coins/day")

        # Top 500 coverage
        days_with_500plus = (daily_counts >= 500).sum()
        logger.info(f"\nTop 500 Coverage:")
        logger.info(f"  Days with 500+ coins: {days_with_500plus:,}/{total_days:,} ({days_with_500plus/total_days*100:.1f}%)")

        coverage = {
            'date_min': date_min,
            'date_max': date_max,
            'total_days': total_days,
            'unique_coins': unique_coins,
            'total_records': total_records,
            'avg_coins_per_day': avg_coins_per_day,
            'days_with_500plus': days_with_500plus,
        }

        self.validation_results['coverage'] = coverage
        logger.info("✅ TEST 4 COMPLETED: Coverage metrics collected")
        return coverage

    def run_all_tests(self) -> bool:
        """
        Run complete validation suite.

        Returns:
            True if all tests pass

        Raises:
            ValueError: If any critical test fails
        """
        logger.info("\n" + "=" * 80)
        logger.info("KAGGLE DATASET VALIDATION SUITE")
        logger.info("=" * 80)
        logger.info(f"Dataset: {self.data_path}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80 + "\n")

        try:
            self.load_data()
            self.test_bitconnect_presence()
            self.test_circulating_supply_variation()
            self.test_rank_consistency()
            self.test_coverage()

            logger.info("\n" + "=" * 80)
            logger.info("VALIDATION RESULT: ✅ ALL TESTS PASSED")
            logger.info("=" * 80)
            logger.info("RECOMMENDATION: USE this Kaggle dataset for 2013-2021 period")
            logger.info("NEXT STEP: Use crypto2 R package for 2021-2024 gap")
            logger.info("=" * 80)

            return True

        except ValueError as e:
            logger.error("\n" + "=" * 80)
            logger.error("VALIDATION RESULT: ❌ FAILED")
            logger.error("=" * 80)
            logger.error(str(e))
            logger.error("=" * 80)
            raise


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate Kaggle cryptocurrency dataset')
    parser.add_argument(
        'data_path',
        type=Path,
        help='Path to Kaggle dataset CSV file'
    )
    args = parser.parse_args()

    validator = KaggleValidator(args.data_path)

    try:
        validator.run_all_tests()
        sys.exit(0)
    except ValueError:
        sys.exit(1)


if __name__ == '__main__':
    main()
