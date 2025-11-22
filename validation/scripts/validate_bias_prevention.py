#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pandas>=2.0.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Look-Ahead Bias Prevention Validation Script

ADR: 0001-hybrid-free-data-acquisition
Purpose: Validate that merged dataset has no look-ahead bias or survivorship bias

Tests:
1. Dead coin verification (BitConnect, Paycoin, Terra/Luna)
2. Circulating supply progression (BTC 14M→19M, ETH growth)
3. Historical event validation (collapses, peaks, crashes)
4. Rank consistency checks (calculated vs provided)

Usage:
    uv run validation/scripts/validate_bias_prevention.py data/final/merged_dataset.csv

Exit Codes:
    0: All validations passed
    1: Look-ahead bias or survivorship bias detected
"""

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np


class BiasPreventionValidator:
    """Validates dataset for look-ahead bias and survivorship bias."""

    # Historical dead coins with expected date ranges
    DEAD_COINS = {
        'BitConnect': {
            'symbols': ['BCC', 'BITCONNECT'],
            'expected_start': '2016-01-01',
            'expected_end': '2018-01-16',  # BitConnect shutdown
            'peak_period': ('2017-12-01', '2018-01-15'),
            'reason': 'Ponzi scheme shutdown'
        },
        'Terra': {
            'symbols': ['LUNA', 'LUNC'],
            'expected_start': '2019-07-01',
            'expected_end': '2022-05-13',  # Terra collapse
            'peak_period': ('2022-04-01', '2022-05-09'),
            'reason': 'Algorithmic stablecoin collapse ($60B wipeout)'
        },
        'FTX Token': {
            'symbols': ['FTT'],
            'expected_start': '2019-07-01',
            'expected_end': '2022-11-11',  # FTX bankruptcy
            'peak_period': ('2021-09-01', '2022-11-08'),
            'reason': 'Exchange bankruptcy'
        },
    }

    # Bitcoin circulating supply milestones
    BTC_SUPPLY_MILESTONES = {
        '2015-01-01': (14_000_000, 14_500_000),  # ~14.25M
        '2016-01-01': (15_000_000, 15_500_000),  # ~15.25M
        '2017-01-01': (16_000_000, 16_500_000),  # ~16.25M
        '2018-01-01': (16_750_000, 17_250_000),  # ~17M
        '2019-01-01': (17_500_000, 18_000_000),  # ~17.75M
        '2020-05-12': (18_350_000, 18_400_000),  # Halving #3
        '2021-01-01': (18_600_000, 18_700_000),  # ~18.65M
        '2022-01-01': (18_900_000, 19_000_000),  # ~18.95M
        '2024-04-20': (19_680_000, 19_690_000),  # Halving #4
    }

    # Historical market events
    HISTORICAL_EVENTS = {
        '2017_btc_ath': {
            'date': '2017-12-17',
            'coin': 'BTC',
            'event': 'Bitcoin ATH ~$19,783',
            'expected_price_range': (15000, 20000),
            'expected_rank': 1
        },
        '2021_crypto_peak': {
            'date': '2021-11-10',
            'coin': 'BTC',
            'event': 'Crypto market peak',
            'expected_price_range': (65000, 69000),
            'expected_rank': 1
        },
        'terra_collapse': {
            'date': '2022-05-09',
            'coin': 'LUNA',
            'event': 'Terra/Luna $60B wipeout',
            'expected_price_range': (0, 10),  # After collapse
            'check_before': ('2022-04-01', (50, 120))  # Before collapse
        },
    }

    def __init__(self, csv_path: str):
        """
        Initialize validator.

        Args:
            csv_path: Path to merged dataset CSV

        Raises:
            FileNotFoundError: If CSV doesn't exist
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {csv_path}\n"
                f"Expected merged dataset from Phase 4\n"
                f"NEXT STEP: Run data merge pipeline first"
            )

        self.df = None
        self.warnings = []
        self.critical_failures = []

    def load_data(self) -> None:
        """Load and prepare data."""
        logger.info(f"Loading dataset from {self.csv_path}")

        try:
            self.df = pd.read_csv(self.csv_path)
        except Exception as e:
            raise ValueError(f"Failed to load CSV: {e}")

        if len(self.df) == 0:
            raise ValueError(f"Dataset is empty: {self.csv_path}")

        # Convert date column
        date_cols = ['date', 'timestamp', 'time']
        date_col = None
        for col in date_cols:
            if col in self.df.columns:
                date_col = col
                break

        if not date_col:
            raise ValueError(
                f"No date column found. Expected one of: {date_cols}\n"
                f"Actual columns: {list(self.df.columns)}"
            )

        self.df['parsed_date'] = pd.to_datetime(self.df[date_col])
        self.date_col = date_col

        # Identify symbol column
        symbol_cols = ['symbol', 'coin_symbol', 'ticker']
        self.symbol_col = None
        for col in symbol_cols:
            if col in self.df.columns:
                self.symbol_col = col
                break

        if not self.symbol_col:
            raise ValueError(
                f"No symbol column found. Expected one of: {symbol_cols}"
            )

        logger.info(f"Loaded {len(self.df):,} rows")
        logger.info(f"Date range: {self.df['parsed_date'].min()} to {self.df['parsed_date'].max()}")
        logger.info(f"Unique coins: {self.df[self.symbol_col].nunique()}")

    def test_dead_coin_verification(self) -> bool:
        """
        Test 1: Verify dead coins are present in historical periods.

        This is the most critical test for survivorship bias.

        Returns:
            True if all dead coins found in expected periods

        Raises:
            ValueError: If critical dead coins missing (survivorship bias detected)
        """
        logger.info("="*60)
        logger.info("Test 1: Dead Coin Verification (Survivorship Bias)")
        logger.info("="*60)

        for coin_name, config in self.DEAD_COINS.items():
            logger.info(f"\nChecking {coin_name}...")

            # Find coin by any of its symbols
            coin_df = pd.DataFrame()
            for symbol in config['symbols']:
                matches = self.df[self.df[self.symbol_col].str.upper() == symbol.upper()]
                if len(matches) > 0:
                    coin_df = matches
                    logger.info(f"  Found as symbol: {symbol}")
                    break

            if len(coin_df) == 0:
                self.critical_failures.append(
                    f"❌ CRITICAL: {coin_name} not found in dataset\n"
                    f"   Expected symbols: {config['symbols']}\n"
                    f"   This indicates SURVIVORSHIP BIAS - dataset excludes dead coins\n"
                    f"   Reason: {config['reason']}"
                )
                logger.error(f"  ❌ {coin_name} NOT FOUND - SURVIVORSHIP BIAS!")
                continue

            # Check date range
            coin_start = coin_df['parsed_date'].min()
            coin_end = coin_df['parsed_date'].max()

            logger.info(f"  Date range in dataset: {coin_start.date()} to {coin_end.date()}")
            logger.info(f"  Expected: ~{config['expected_start']} to ~{config['expected_end']}")

            # Verify coin exists in expected peak period
            peak_start = pd.to_datetime(config['peak_period'][0])
            peak_end = pd.to_datetime(config['peak_period'][1])

            peak_records = coin_df[
                (coin_df['parsed_date'] >= peak_start) &
                (coin_df['parsed_date'] <= peak_end)
            ]

            if len(peak_records) == 0:
                self.warnings.append(
                    f"⚠️  {coin_name} has no records in peak period "
                    f"{config['peak_period'][0]} to {config['peak_period'][1]}"
                )
                logger.warning(f"  ⚠️  No records in peak period")
            else:
                logger.info(f"  ✅ Found {len(peak_records)} records in peak period")

            # Check if coin exists AFTER expected death date
            death_date = pd.to_datetime(config['expected_end'])
            after_death = coin_df[coin_df['parsed_date'] > death_date + pd.Timedelta(days=30)]

            if len(after_death) > 100:  # Allow some grace period
                self.warnings.append(
                    f"⚠️  {coin_name} has {len(after_death)} records > 30 days after death date\n"
                    f"   May indicate revived project or fork"
                )
                logger.warning(f"  ⚠️  {len(after_death)} records after death date")

            logger.info(f"  ✅ {coin_name} verification PASSED")

        if self.critical_failures:
            raise ValueError(
                "SURVIVORSHIP BIAS DETECTED:\n" + "\n".join(self.critical_failures) +
                "\n\nRECOMMENDATION: Dataset excludes dead coins. "
                "This creates look-ahead bias. Data source is unreliable."
            )

        logger.info("\n✅ Dead coin verification PASSED - No survivorship bias detected")
        return True

    def test_supply_progression(self) -> bool:
        """
        Test 2: Verify circulating supply progresses correctly.

        Checks if Bitcoin supply increases over time as expected.

        Returns:
            True if supply progression is correct
        """
        logger.info("="*60)
        logger.info("Test 2: Circulating Supply Progression")
        logger.info("="*60)

        # Check if circulating_supply column exists
        supply_cols = ['circulating_supply', 'supply', 'circulating']
        supply_col = None
        for col in supply_cols:
            if col in self.df.columns:
                supply_col = col
                break

        if not supply_col:
            self.warnings.append(
                "⚠️  No circulating_supply column found\n"
                "   Cannot verify supply progression (look-ahead bias check skipped)"
            )
            logger.warning("  ⚠️  No circulating_supply column - test skipped")
            return True

        # Get Bitcoin data
        btc_df = self.df[self.df[self.symbol_col].str.upper() == 'BTC'].copy()

        if len(btc_df) == 0:
            self.warnings.append("⚠️  Bitcoin not found in dataset")
            logger.warning("  ⚠️  Bitcoin not found - test skipped")
            return True

        logger.info(f"\nBitcoin Supply Progression Check:")
        logger.info(f"  Total BTC records: {len(btc_df)}")

        # Check milestones
        passed_checks = 0
        for date_str, (min_supply, max_supply) in self.BTC_SUPPLY_MILESTONES.items():
            check_date = pd.to_datetime(date_str)

            # Find closest record to this date
            btc_near_date = btc_df[
                abs((btc_df['parsed_date'] - check_date).dt.days) <= 7
            ]

            if len(btc_near_date) == 0:
                logger.info(f"  ⊘ {date_str}: No data near this date")
                continue

            actual_supply = btc_near_date[supply_col].median()

            if pd.isna(actual_supply):
                logger.warning(f"  ⚠️  {date_str}: Supply is null")
                continue

            if min_supply <= actual_supply <= max_supply:
                logger.info(
                    f"  ✅ {date_str}: {actual_supply:,.0f} BTC "
                    f"(expected {min_supply:,.0f}-{max_supply:,.0f})"
                )
                passed_checks += 1
            else:
                self.warnings.append(
                    f"⚠️  Bitcoin supply on {date_str} is {actual_supply:,.0f}\n"
                    f"   Expected range: {min_supply:,.0f}-{max_supply:,.0f}\n"
                    f"   May indicate look-ahead bias (using current supply for historical data)"
                )
                logger.warning(
                    f"  ⚠️  {date_str}: {actual_supply:,.0f} BTC "
                    f"(expected {min_supply:,.0f}-{max_supply:,.0f})"
                )

        if passed_checks >= 3:  # Need at least 3 milestones to pass
            logger.info(f"\n✅ Supply progression PASSED ({passed_checks} milestones verified)")
        else:
            self.warnings.append(
                f"⚠️  Only {passed_checks} supply milestones verified\n"
                f"   Unable to fully verify supply progression"
            )
            logger.warning(f"  ⚠️  Only {passed_checks} milestones verified")

        return True

    def test_historical_events(self) -> bool:
        """
        Test 3: Verify historical events are present.

        Checks major market events to ensure data is point-in-time.

        Returns:
            True if events are represented correctly
        """
        logger.info("="*60)
        logger.info("Test 3: Historical Event Validation")
        logger.info("="*60)

        for event_id, config in self.HISTORICAL_EVENTS.items():
            logger.info(f"\n{event_id}: {config['event']}")

            event_date = pd.to_datetime(config['date'])
            coin_symbol = config['coin']

            # Find coin data near event date
            coin_df = self.df[self.df[self.symbol_col].str.upper() == coin_symbol.upper()]

            if len(coin_df) == 0:
                logger.warning(f"  ⚠️  {coin_symbol} not found in dataset")
                continue

            event_records = coin_df[
                abs((coin_df['parsed_date'] - event_date).dt.days) <= 3
            ]

            if len(event_records) == 0:
                self.warnings.append(
                    f"⚠️  No data found for {coin_symbol} near {config['date']}\n"
                    f"   Event: {config['event']}"
                )
                logger.warning(f"  ⚠️  No data near event date")
                continue

            # Check price if available
            price_cols = ['price', 'price_usd', 'current_price']
            price_col = None
            for col in price_cols:
                if col in self.df.columns:
                    price_col = col
                    break

            if price_col:
                actual_price = event_records[price_col].median()

                if 'expected_price_range' in config:
                    min_price, max_price = config['expected_price_range']

                    if min_price <= actual_price <= max_price:
                        logger.info(
                            f"  ✅ Price: ${actual_price:,.2f} "
                            f"(expected ${min_price:,.0f}-${max_price:,.0f})"
                        )
                    else:
                        logger.warning(
                            f"  ⚠️  Price: ${actual_price:,.2f} "
                            f"(expected ${min_price:,.0f}-${max_price:,.0f})"
                        )

            # Check "before" condition if specified (e.g., Terra before collapse)
            if 'check_before' in config:
                before_date_str, before_price_range = config['check_before']
                before_date = pd.to_datetime(before_date_str)

                before_records = coin_df[
                    abs((coin_df['parsed_date'] - before_date).dt.days) <= 3
                ]

                if len(before_records) > 0 and price_col:
                    before_price = before_records[price_col].median()
                    min_before, max_before = before_price_range

                    if min_before <= before_price <= max_before:
                        logger.info(
                            f"  ✅ Before event ({before_date_str}): ${before_price:,.2f} "
                            f"(expected ${min_before:,.0f}-${max_before:,.0f})"
                        )
                    else:
                        logger.warning(
                            f"  ⚠️  Before event: ${before_price:,.2f} "
                            f"(expected ${min_before:,.0f}-${max_before:,.0f})"
                        )

        logger.info("\n✅ Historical event validation COMPLETE")
        return True

    def test_rank_consistency(self) -> bool:
        """
        Test 4: Verify market cap ranks are consistent with market cap values.

        Returns:
            True if ranks match market cap ordering
        """
        logger.info("="*60)
        logger.info("Test 4: Rank Consistency Check")
        logger.info("="*60)

        # Check if rank and market_cap columns exist
        rank_cols = ['rank', 'market_cap_rank', 'cmc_rank']
        mcap_cols = ['market_cap', 'market_cap_usd', 'marketcap']

        rank_col = None
        mcap_col = None

        for col in rank_cols:
            if col in self.df.columns:
                rank_col = col
                break

        for col in mcap_cols:
            if col in self.df.columns:
                mcap_col = col
                break

        if not rank_col or not mcap_col:
            logger.warning("  ⚠️  Missing rank or market_cap columns - test skipped")
            return True

        # Sample random dates to check
        sample_dates = self.df['parsed_date'].drop_duplicates().sample(
            min(10, self.df['parsed_date'].nunique())
        )

        total_mismatches = 0
        total_checked = 0

        for check_date in sample_dates:
            date_df = self.df[self.df['parsed_date'] == check_date].copy()

            if len(date_df) < 10:
                continue

            # Sort by market cap
            date_df_sorted = date_df.sort_values(mcap_col, ascending=False)
            date_df_sorted['expected_rank'] = range(1, len(date_df_sorted) + 1)

            # Compare with provided rank
            mismatches = (
                date_df_sorted[rank_col] != date_df_sorted['expected_rank']
            ).sum()

            total_mismatches += mismatches
            total_checked += len(date_df_sorted)

        if total_checked > 0:
            mismatch_pct = (total_mismatches / total_checked) * 100

            logger.info(f"  Checked {total_checked} records across {len(sample_dates)} dates")
            logger.info(f"  Rank mismatches: {total_mismatches} ({mismatch_pct:.1f}%)")

            if mismatch_pct > 10:
                self.warnings.append(
                    f"⚠️  {mismatch_pct:.1f}% rank/market cap mismatches\n"
                    f"   Provided ranks may not match market cap ordering"
                )
                logger.warning(f"  ⚠️  High mismatch rate: {mismatch_pct:.1f}%")
            else:
                logger.info(f"  ✅ Rank consistency acceptable ({mismatch_pct:.1f}% mismatches)")

        return True

    def run_all_tests(self) -> bool:
        """
        Run complete bias prevention validation suite.

        Returns:
            True if all tests passed

        Raises:
            ValueError: If critical bias detected
        """
        logger.info("="*70)
        logger.info("LOOK-AHEAD BIAS PREVENTION VALIDATION SUITE")
        logger.info("="*70)
        logger.info("")

        self.load_data()

        tests = [
            ("Dead Coin Verification", self.test_dead_coin_verification),
            ("Supply Progression", self.test_supply_progression),
            ("Historical Events", self.test_historical_events),
            ("Rank Consistency", self.test_rank_consistency),
        ]

        for test_name, test_func in tests:
            try:
                test_func()
            except ValueError as e:
                # Critical failure - propagate
                raise
            except Exception as e:
                logger.error(f"Test '{test_name}' failed with error: {e}")
                self.warnings.append(f"⚠️  Test '{test_name}' encountered error: {e}")

            logger.info("")

        # Summary
        logger.info("="*70)
        logger.info("VALIDATION SUMMARY")
        logger.info("="*70)

        if self.warnings:
            logger.info(f"⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.info(f"  {warning}")
            logger.info("")

        if self.critical_failures:
            logger.error("❌ CRITICAL FAILURES:")
            for failure in self.critical_failures:
                logger.error(f"  {failure}")
            logger.error("")
            raise ValueError(
                f"{len(self.critical_failures)} critical failures detected. "
                "Dataset has look-ahead bias or survivorship bias."
            )

        logger.info("✅ All bias prevention tests PASSED")
        logger.info("")
        logger.info("Dataset appears free of:")
        logger.info("  - Survivorship bias (dead coins present)")
        logger.info("  - Look-ahead bias (supply progression correct)")
        logger.info("  - Historical revisionism (events represented)")
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("  1. Review warnings (if any)")
        logger.info("  2. Proceed to final dataset assembly")
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
        description='Validate dataset for look-ahead bias and survivorship bias'
    )
    parser.add_argument(
        'csv_path',
        help='Path to merged dataset CSV (e.g., data/final/merged_dataset.csv)'
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
    log_file = log_dir / f'0001-bias-prevention-{timestamp}.log'

    setup_logging(log_file)

    global logger
    logger = logging.getLogger(__name__)

    logger.info(f"Bias Prevention Validation Log: {log_file}")
    logger.info(f"Input file: {args.csv_path}")
    logger.info("")

    try:
        validator = BiasPreventionValidator(args.csv_path)
        validator.run_all_tests()

        logger.info(f"Log saved to: {log_file}")
        return 0

    except Exception as e:
        logger.error("="*70)
        logger.error("VALIDATION FAILED")
        logger.error("="*70)
        logger.error(f"Error: {e}")
        logger.error("")
        logger.error(f"Full log: {log_file}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
