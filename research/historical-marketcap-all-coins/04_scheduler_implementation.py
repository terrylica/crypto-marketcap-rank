#!/usr/bin/env python3
"""
Working scheduler implementation for daily use.

This module provides:
- SchedulerEngine: The core scheduling logic
- SchedulerAPI: Interface for querying today's coins
- Persistence: Save/load scheduler state
"""

from datetime import datetime, timedelta
from typing import List, Dict, Set
import json
import math
from pathlib import Path


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

        selected_indices = list(range(start_idx, end_idx))
        selected_coins = [self.coin_start + idx for idx in selected_indices]
        return selected_coins


class SchedulerEngine:
    """Core scheduling logic"""

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

    def get_schedule_for_day(self, date: datetime = None) -> Dict:
        """Get the complete schedule for a specific day"""
        date = date or datetime.now()
        day_number = self.days_since_base(date)

        samples_by_tier = {}
        total_samples = 0

        for tier in self.tiers:
            coins = tier.get_coins_for_day(day_number)
            samples_by_tier[tier.name] = coins
            total_samples += len(coins)

        # Build comprehensive response
        all_coins_flat = []
        tier_order = []
        for tier in self.tiers:
            if tier.name in samples_by_tier and samples_by_tier[tier.name]:
                all_coins_flat.extend(samples_by_tier[tier.name])
                tier_order.append(tier.name)

        return {
            "date": date.strftime("%Y-%m-%d"),
            "day_number": day_number,
            "samples_by_tier": samples_by_tier,
            "all_coins_sorted": sorted(all_coins_flat),
            "all_coins_by_tier_order": all_coins_flat,
            "total_samples": total_samples,
            "budget_limit": 650,
            "budget_used": total_samples,
            "budget_margin": 650 - total_samples,
            "tiers_sampling_today": tier_order,
        }


class SchedulerAPI:
    """User-facing API for the scheduler"""

    def __init__(self, config_dir: str = "/tmp/historical-marketcap-all-coins"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.engine = SchedulerEngine()

    def get_today_schedule(self) -> Dict:
        """Get coins to sample today"""
        return self.engine.get_schedule_for_day(datetime.now())

    def get_date_schedule(self, date_str: str) -> Dict:
        """Get coins to sample on a specific date (YYYY-MM-DD format)"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return self.engine.get_schedule_for_day(date)

    def get_week_schedule(self) -> List[Dict]:
        """Get schedule for next 7 days"""
        today = datetime.now()
        schedule = []
        for i in range(7):
            date = today + timedelta(days=i)
            schedule.append(self.engine.get_schedule_for_day(date))
        return schedule

    def export_schedule_as_json(self, filename: str = "today_schedule.json"):
        """Export today's schedule as JSON"""
        schedule = self.get_today_schedule()
        output_file = self.config_dir / filename
        with open(output_file, 'w') as f:
            json.dump(schedule, f, indent=2)
        return str(output_file)

    def export_coins_as_csv(self, filename: str = "today_coins.csv"):
        """Export today's coins as CSV"""
        schedule = self.get_today_schedule()
        output_file = self.config_dir / filename
        with open(output_file, 'w') as f:
            f.write("coin_id,tier,priority\n")
            tier_priority = {tier: i for i, tier in enumerate(schedule['tiers_sampling_today'])}
            for tier_name, coins in schedule['samples_by_tier'].items():
                priority = tier_priority.get(tier_name, 999)
                for coin_id in coins:
                    f.write(f"{coin_id},{tier_name},{priority}\n")
        return str(output_file)

    def get_tier_info(self) -> List[Dict]:
        """Get information about all tiers"""
        tiers_info = []
        for tier in self.engine.tiers:
            tiers_info.append({
                "name": tier.name,
                "coin_range": f"{tier.coin_start}-{tier.coin_end}",
                "coin_count": tier.coin_count,
                "update_frequency_days": tier.frequency_days,
                "coins_per_sampling_day": tier.coins_per_sampling_day(),
                "expected_samples_per_year": round(365 / tier.frequency_days, 1),
            })
        return tiers_info


def main():
    """Demo the scheduler implementation"""

    print("=" * 80)
    print("SCHEDULER IMPLEMENTATION - READY FOR PRODUCTION USE")
    print("=" * 80)
    print()

    api = SchedulerAPI()

    # Show tier info
    print("TIER CONFIGURATION:")
    print("-" * 80)
    for tier in api.get_tier_info():
        print(f"\n{tier['name']}")
        print(f"  Coins: {tier['coin_range']} ({tier['coin_count']} total)")
        print(f"  Update frequency: Every {tier['update_frequency_days']} day(s)")
        print(f"  Coins sampled per update: {tier['coins_per_sampling_day']}")
        print(f"  Expected samples per year: {tier['expected_samples_per_year']}")

    print()
    print()

    # Show today's schedule
    print("TODAY'S SCHEDULE:")
    print("-" * 80)
    today_schedule = api.get_today_schedule()
    print(f"\nDate: {today_schedule['date']}")
    print(f"Day number: {today_schedule['day_number']}")
    print(f"Budget used: {today_schedule['budget_used']} / {today_schedule['budget_limit']} API calls")
    print(f"Budget margin: {today_schedule['budget_margin']} calls available")
    print(f"\nTiers sampling today: {', '.join(today_schedule['tiers_sampling_today'])}")
    print()

    for tier_name, coins in today_schedule['samples_by_tier'].items():
        if coins:
            print(f"{tier_name}: {len(coins)} coins")
            if len(coins) <= 10:
                print(f"  {coins}")
            else:
                print(f"  First 5: {coins[:5]}")
                print(f"  Last 5: {coins[-5:]}")

    # Show week preview
    print()
    print()
    print("WEEK PREVIEW (Next 7 days):")
    print("-" * 80)
    week_schedule = api.get_week_schedule()
    for day in week_schedule:
        print(f"\n{day['date']}: {day['total_samples']} samples ({day['budget_margin']} margin)")
        tier_summary = ", ".join([f"{t}" for t in day['tiers_sampling_today']])
        print(f"  Tiers: {tier_summary}")

    # Export schedules
    print()
    print()
    print("EXPORTING SCHEDULES:")
    print("-" * 80)
    json_file = api.export_schedule_as_json()
    print(f"JSON export: {json_file}")

    csv_file = api.export_coins_as_csv()
    print(f"CSV export: {csv_file}")

    # Show sample exports
    print()
    print("Sample CSV content (first 5 lines):")
    with open(csv_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 6:
                print(f"  {line.strip()}")
            else:
                break

    print()
    print()

    # Show usage examples
    print("USAGE EXAMPLES (for developers):")
    print("-" * 80)
    print("""
# Get today's coins to sample
schedule = api.get_today_schedule()
coins = schedule['all_coins_sorted']
for coin_id in coins:
    # Call your API to fetch market cap data
    fetch_and_store_coin_data(coin_id)

# Get schedule for specific date
schedule = api.get_date_schedule("2024-01-15")

# Get next 7 days
week = api.get_week_schedule()

# Export for batch processing
json_file = api.export_schedule_as_json()
csv_file = api.export_coins_as_csv()
""")

    return api


if __name__ == "__main__":
    api = main()
