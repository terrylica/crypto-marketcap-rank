#!/usr/bin/env python3
"""
Improved rotation scheduler with proper coin cycling.

This version ensures:
1. Every coin in a tier eventually gets sampled
2. Rotation spreads coins evenly across update frequency
3. Deterministic and reproducible scheduling
4. Proper fairness guarantees
"""

from datetime import datetime, timedelta
from typing import List, Set, Dict
import json
import math


class CoinTier:
    """Represents a sampling tier"""

    def __init__(self, name: str, coin_start: int, coin_end: int, frequency_days: int):
        self.name = name
        self.coin_start = coin_start
        self.coin_end = coin_end
        self.frequency_days = frequency_days
        self.coin_count = coin_end - coin_start + 1

    def coins_per_sampling_day(self) -> int:
        """How many coins from this tier on a sampling day"""
        return math.ceil(self.coin_count / self.frequency_days)

    def get_coins_for_day(self, day_number: int) -> List[int]:
        """Get coins to sample on a specific day"""
        # Only sample on days aligned with frequency
        if day_number % self.frequency_days != 0:
            return []

        # Which rotation cycle are we in?
        cycle_number = day_number // self.frequency_days
        coins_per_day = self.coins_per_sampling_day()

        # Get the coins for this cycle
        cycle_offset = (cycle_number % self.frequency_days)
        start_idx = cycle_offset * coins_per_day
        end_idx = min(start_idx + coins_per_day, self.coin_count)

        # Handle wraparound for last batch
        if end_idx < start_idx + coins_per_day:
            # Last batch may be smaller
            selected_indices = list(range(start_idx, end_idx))
        else:
            selected_indices = list(range(start_idx, end_idx))

        selected_coins = [self.coin_start + idx for idx in selected_indices]
        return selected_coins


class ImprovedScheduler:
    """Improved scheduler with proper rotation guarantees"""

    def __init__(self, base_date: datetime = None):
        self.base_date = base_date or datetime(2024, 1, 1)
        self.tiers = [
            CoinTier("Tier1_MegaCap", 1, 10, 1),
            CoinTier("Tier2_LargeCap", 11, 50, 1),
            CoinTier("Tier3_MidCap", 51, 200, 2),
            CoinTier("Tier4_SmallCap", 201, 1000, 7),
            CoinTier("Tier5_MicroCap", 1001, 5000, 30),
            CoinTier("Tier6_Penny", 5001, 13532, 90),
        ]

    def days_since_base(self, date: datetime = None) -> int:
        """Days since base date"""
        date = date or datetime.now()
        return (date - self.base_date).days

    def get_schedule_for_day(self, date: datetime = None) -> dict:
        """Get the sampling schedule for a specific day"""
        date = date or datetime.now()
        day_number = self.days_since_base(date)

        samples_by_tier = {}
        total_samples = 0

        for tier in self.tiers:
            coins = tier.get_coins_for_day(day_number)
            samples_by_tier[tier.name] = coins
            total_samples += len(coins)

        return {
            "date": date.strftime("%Y-%m-%d"),
            "day_number": day_number,
            "samples_by_tier": samples_by_tier,
            "total_samples": total_samples,
            "budget_margin": 650 - total_samples,
        }

    def analyze_full_coverage(self, num_days: int = 450) -> dict:
        """
        Analyze coverage metrics over a period.

        Note: 450 days captures 5 complete cycles of the longest tier (90 day)
        """
        start_date = self.base_date
        end_date = start_date + timedelta(days=num_days)

        # Track sampling frequency for each coin
        coin_sample_counts = {}

        current = start_date
        day_count = 0
        tier_daily_calls = {tier.name: [] for tier in self.tiers}

        while current <= end_date:
            schedule = self.get_schedule_for_day(current)

            for tier_name, coins in schedule['samples_by_tier'].items():
                tier_daily_calls[tier_name].append(len(coins))
                for coin in coins:
                    coin_sample_counts[coin] = coin_sample_counts.get(coin, 0) + 1

            current += timedelta(days=1)
            day_count += 1

        # Organize by tier
        tier_stats = {}
        for tier in self.tiers:
            coin_ids = list(range(tier.coin_start, tier.coin_end + 1))
            tier_counts = [coin_sample_counts.get(cid, 0) for cid in coin_ids]

            tier_stats[tier.name] = {
                "coin_count": len(coin_ids),
                "expected_samples_per_coin": round(day_count / tier.frequency_days, 1),
                "min_samples": min(tier_counts) if tier_counts else 0,
                "max_samples": max(tier_counts) if tier_counts else 0,
                "avg_samples": round(sum(tier_counts) / len(tier_counts), 2) if tier_counts else 0,
                "std_dev": round(self._std_dev(tier_counts), 2) if tier_counts else 0,
            }

        all_coin_ids = set(range(1, 13533))
        sampled_coins = set(coin_sample_counts.keys())

        analysis = {
            "period_days": num_days,
            "total_days": day_count,
            "total_coins": 13532,
            "unique_coins_sampled": len(sampled_coins),
            "coverage_percent": round((len(sampled_coins) / 13532) * 100, 2),
            "total_api_calls": sum(sum(calls) for calls in tier_daily_calls.values()),
            "avg_calls_per_day": round(sum(sum(calls) for calls in tier_daily_calls.values()) / day_count, 1),
            "by_tier": tier_stats,
            "tier_daily_call_stats": {
                tier.name: {
                    "min": min(tier_daily_calls[tier.name]),
                    "max": max(tier_daily_calls[tier.name]),
                    "avg": round(sum(tier_daily_calls[tier.name]) / len(tier_daily_calls[tier.name]), 1),
                }
                for tier in self.tiers
            },
        }

        return analysis

    @staticmethod
    def _std_dev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)


def main():
    """Demonstrate improved scheduler"""

    print("=" * 80)
    print("IMPROVED ROTATION SCHEDULER WITH FAIR COIN CYCLING")
    print("=" * 80)
    print()

    scheduler = ImprovedScheduler()

    # Show example schedules
    print("EXAMPLE SCHEDULES (First 10 days):")
    print("-" * 80)
    for i in range(10):
        date = scheduler.base_date + timedelta(days=i)
        schedule = scheduler.get_schedule_for_day(date)
        print(f"\nDate: {schedule['date']} (Day {schedule['day_number']})")
        print(f"  Total samples: {schedule['total_samples']}/650")
        for tier_name, coins in schedule['samples_by_tier'].items():
            if coins:
                print(f"  {tier_name}: {len(coins)} coins")
                if len(coins) <= 5:
                    print(f"    Coins: {coins}")
                else:
                    print(f"    First 5: {coins[:5]}")

    print()
    print()

    # Analyze different coverage periods
    for days in [90, 180, 365, 450]:
        print(f"COVERAGE ANALYSIS ({days}-day period):")
        print("-" * 80)
        analysis = scheduler.analyze_full_coverage(num_days=days)

        print(f"Period: {analysis['period_days']} days ({analysis['total_days']} actual days)")
        print(f"Coins sampled: {analysis['unique_coins_sampled']} / {analysis['total_coins']} ({analysis['coverage_percent']}%)")
        print(f"Total API calls: {analysis['total_api_calls']:,}")
        print(f"Average calls per day: {analysis['avg_calls_per_day']}")
        print()

        print("Sampling fairness by tier:")
        for tier_name, stats in analysis['by_tier'].items():
            print(f"\n  {tier_name}:")
            print(f"    Coins in tier: {stats['coin_count']}")
            print(f"    Expected samples per coin: {stats['expected_samples_per_coin']}")
            print(f"    Actual samples per coin (min/max/avg): {stats['min_samples']}/{stats['max_samples']}/{stats['avg_samples']}")
            print(f"    Fairness std dev: {stats['std_dev']}")

        print()
        print()

    # Save detailed output
    scheduler_config = {
        "base_date": scheduler.base_date.strftime("%Y-%m-%d"),
        "tiers": [
            {
                "name": tier.name,
                "coin_range": f"{tier.coin_start}-{tier.coin_end}",
                "coin_count": tier.coin_count,
                "update_frequency_days": tier.frequency_days,
                "coins_per_sampling_day": tier.coins_per_sampling_day(),
            }
            for tier in scheduler.tiers
        ],
    }

    output = {
        "scheduler_config": scheduler_config,
        "coverage_90_days": scheduler.analyze_full_coverage(90),
        "coverage_365_days": scheduler.analyze_full_coverage(365),
        "coverage_450_days": scheduler.analyze_full_coverage(450),
    }

    output_file = "/tmp/historical-marketcap-all-coins/improved_scheduler.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Detailed analysis saved to: {output_file}")

    return scheduler, output


if __name__ == "__main__":
    scheduler, output = main()
