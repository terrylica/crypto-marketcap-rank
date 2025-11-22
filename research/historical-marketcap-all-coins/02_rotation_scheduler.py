#!/usr/bin/env python3
"""
Rotation scheduler for tier-based sampling.

This algorithm ensures:
1. Each tier gets sampled according to its frequency
2. Within a tier, coins rotate to maximize coverage
3. Deterministic scheduling (same output for same date)
4. Handles uneven distributions elegantly
"""

from datetime import datetime, timedelta
from typing import List, Set, Tuple
import json
import math


class RotationScheduler:
    """Schedule which coins to sample each day based on tier membership"""

    # Tier definitions: (name, coin_range_start, coin_range_end, update_frequency_days)
    TIERS = [
        ("Tier1_MegaCap", 1, 10, 1),
        ("Tier2_LargeCap", 11, 50, 1),
        ("Tier3_MidCap", 51, 200, 2),
        ("Tier4_SmallCap", 201, 1000, 7),
        ("Tier5_MicroCap", 1001, 5000, 30),
        ("Tier6_Penny", 5001, 13532, 90),
    ]

    def __init__(self, reference_date: datetime = None):
        """
        Initialize scheduler.

        Args:
            reference_date: The date to base calculations on (default: today)
        """
        self.reference_date = reference_date or datetime.now()
        self.base_date = datetime(2024, 1, 1)  # Fixed base for determinism

    def days_since_base(self, date: datetime = None) -> int:
        """Days since base date (for deterministic rotation)"""
        date = date or self.reference_date
        return (date - self.base_date).days

    def get_coins_for_day(self, date: datetime = None) -> dict:
        """
        Get the list of coins to sample on a given day.

        Returns:
            {
                "date": str,
                "tier_name": ["coin_ids"],
                "summary": {
                    "total_samples": int,
                    "budget_used": int,
                    "budget_margin": int,
                }
            }
        """
        date = date or self.reference_date
        day_num = self.days_since_base(date)

        samples_by_tier = {}
        total_samples = 0

        for tier_name, coin_start, coin_end, frequency_days in self.TIERS:
            coin_count = coin_end - coin_start + 1

            # Determine if this tier samples today
            if day_num % frequency_days != (coin_start - 1) % frequency_days:
                # This tier doesn't sample today
                samples_by_tier[tier_name] = []
                continue

            # This tier samples today - which coins?
            coins_per_sample = math.ceil(coin_count / frequency_days)
            offset = (day_num // frequency_days) % frequency_days

            coin_indices = list(range(coin_count))
            # Rotate indices to get different coins each time
            rotated_indices = (coin_indices[coins_per_sample * offset:] +
                             coin_indices[:coins_per_sample * offset])
            sampled_indices = rotated_indices[:coins_per_sample]

            sampled_coins = [coin_start + idx for idx in sampled_indices]
            samples_by_tier[tier_name] = sampled_coins
            total_samples += len(sampled_coins)

        return {
            "date": date.strftime("%Y-%m-%d"),
            "day_number": day_num,
            "samples_by_tier": samples_by_tier,
            "summary": {
                "total_samples": total_samples,
                "budget_limit": 650,
                "budget_used": total_samples,
                "budget_margin": 650 - total_samples,
            }
        }

    def get_schedule_for_period(self, start_date: datetime, end_date: datetime) -> List[dict]:
        """Get schedule for a date range"""
        schedule = []
        current = start_date
        while current <= end_date:
            schedule.append(self.get_coins_for_day(current))
            current += timedelta(days=1)
        return schedule

    def analyze_coverage(self, num_days: int = 365) -> dict:
        """Analyze coverage statistics over N days"""
        start_date = self.reference_date
        end_date = start_date + timedelta(days=num_days)

        schedule = self.get_schedule_for_period(start_date, end_date)

        # Track sampling frequency for each coin
        coin_sample_counts = {}
        tier_daily_calls = {}

        for day_schedule in schedule:
            for tier_name, coins in day_schedule['samples_by_tier'].items():
                if tier_name not in tier_daily_calls:
                    tier_daily_calls[tier_name] = []
                tier_daily_calls[tier_name].append(len(coins))

                for coin_id in coins:
                    coin_sample_counts[coin_id] = coin_sample_counts.get(coin_id, 0) + 1

        # Calculate statistics
        all_coin_ids = set(range(1, 13533))
        sampled_coins = set(coin_sample_counts.keys())
        unsampled_coins = all_coin_ids - sampled_coins

        coverage = {
            "analysis_period_days": num_days,
            "total_coins": 13532,
            "coins_sampled": len(sampled_coins),
            "coins_not_sampled": len(unsampled_coins),
            "coverage_percent": round((len(sampled_coins) / 13532) * 100, 2),
            "total_api_calls": sum(len(coins) for schedule in schedule for coins in schedule['samples_by_tier'].values()),
            "avg_calls_per_day": round(sum(len(coins) for schedule in schedule for coins in schedule['samples_by_tier'].values()) / num_days, 1),
            "by_tier_daily_calls": {
                tier_name: {
                    "min": min(calls),
                    "max": max(calls),
                    "avg": round(sum(calls) / len(calls), 1),
                }
                for tier_name, calls in tier_daily_calls.items() if calls
            },
            "coin_sample_distribution": {
                "min_samples": min(coin_sample_counts.values()) if coin_sample_counts else 0,
                "max_samples": max(coin_sample_counts.values()) if coin_sample_counts else 0,
                "avg_samples": round(sum(coin_sample_counts.values()) / len(coin_sample_counts), 2) if coin_sample_counts else 0,
            },
            "sample_fairness": {
                "top_10_avg_samples": round(sum(coin_sample_counts.get(i, 0) for i in range(1, 11)) / 10, 1),
                "tier2_avg_samples": round(sum(coin_sample_counts.get(i, 0) for i in range(11, 51)) / 40, 1),
                "tier6_avg_samples": round(sum(coin_sample_counts.get(i, 0) for i in range(5001, 13533)) / 8532, 2),
            },
        }

        return coverage


def main():
    """Demonstrate the rotation scheduler"""

    print("=" * 80)
    print("ROTATION SCHEDULER FOR TIER-BASED COIN SAMPLING")
    print("=" * 80)
    print()

    scheduler = RotationScheduler()

    # Show example schedules for first 10 days
    print("EXAMPLE SCHEDULES (First 10 days):")
    print("-" * 80)
    start_date = datetime(2024, 1, 1)
    for i in range(10):
        date = start_date + timedelta(days=i)
        schedule = scheduler.get_coins_for_day(date)
        print(f"\nDate: {schedule['date']} (Day {schedule['day_number']})")
        print(f"  Budget used: {schedule['summary']['total_samples']}/650")
        for tier_name, coins in schedule['samples_by_tier'].items():
            if coins:
                print(f"  {tier_name}: {len(coins)} coins - {coins[:5]}{('...' if len(coins) > 5 else '')}")

    print()
    print()

    # Analyze coverage
    print("COVERAGE ANALYSIS (90-day period):")
    print("-" * 80)
    coverage = scheduler.analyze_coverage(num_days=90)

    print(f"Period: {coverage['analysis_period_days']} days")
    print(f"Coins sampled: {coverage['coins_sampled']} / {coverage['total_coins']} ({coverage['coverage_percent']}%)")
    print(f"Total API calls: {coverage['total_api_calls']:,}")
    print(f"Average calls per day: {coverage['avg_calls_per_day']}")
    print()

    print("Daily call distribution by tier:")
    for tier_name, stats in coverage['by_tier_daily_calls'].items():
        print(f"  {tier_name}:")
        print(f"    Min/Max/Avg calls: {stats['min']}/{stats['max']}/{stats['avg']}")

    print()
    print("Sample count distribution (per coin over period):")
    print(f"  Min: {coverage['coin_sample_distribution']['min_samples']}")
    print(f"  Max: {coverage['coin_sample_distribution']['max_samples']}")
    print(f"  Avg: {coverage['coin_sample_distribution']['avg_samples']}")

    print()
    print("Fairness metrics (samples by tier importance):")
    print(f"  Top 10 coins avg samples: {coverage['sample_fairness']['top_10_avg_samples']}")
    print(f"  Tier 2 (11-50) avg samples: {coverage['sample_fairness']['tier2_avg_samples']}")
    print(f"  Tier 6 (5001+) avg samples: {coverage['sample_fairness']['tier6_avg_samples']}")

    # 365-day analysis
    print()
    print()
    print("COVERAGE ANALYSIS (365-day period - Full Year):")
    print("-" * 80)
    coverage_year = scheduler.analyze_coverage(num_days=365)

    print(f"Period: {coverage_year['analysis_period_days']} days")
    print(f"Coins sampled: {coverage_year['coins_sampled']} / {coverage_year['total_coins']} ({coverage_year['coverage_percent']}%)")
    print(f"Total API calls: {coverage_year['total_api_calls']:,}")
    print(f"Average calls per day: {coverage_year['avg_calls_per_day']}")

    # Save scheduler demo
    output = {
        "90_day_coverage": coverage,
        "365_day_coverage": coverage_year,
        "tier_definitions": [
            {
                "name": name,
                "coin_range": f"{start}-{end}",
                "update_frequency_days": freq,
            }
            for name, start, end, freq in RotationScheduler.TIERS
        ],
    }

    output_file = "/tmp/historical-marketcap-all-coins/scheduler_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Detailed analysis saved to: {output_file}")
    print()

    return scheduler, coverage, coverage_year


if __name__ == "__main__":
    scheduler, coverage_90, coverage_365 = main()
