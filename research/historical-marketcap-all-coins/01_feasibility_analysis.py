#!/usr/bin/env python3
"""
Feasibility Analysis: Collecting Historical Market Cap for ALL Coins
==================================================================

Calculates the most feasible approach for collecting market cap data
for 13,532+ cryptocurrencies given API constraints.

Strategy: Dynamic data collection vs. historical backfilling
"""

import json
import math
from datetime import datetime, timedelta

# ============================================================================
# CONSTRAINT DEFINITIONS
# ============================================================================

CONSTRAINTS = {
    "total_coins": 13532,
    "free_tier_calls_per_month": 20000,
    "free_tier_calls_per_day": 650,  # ~20000/30 days
    "free_tier_calls_per_hour": 27,   # ~650/24 hours
    "free_tier_calls_per_minute": 0.45, # ~27/60 minutes
    "free_tier_historical_depth": "24 hours",
    "paid_tier_min_calls_per_month": 400000,  # Starter plan
    "paid_tier_historical_depth": "30 days",
    "api_timeout_seconds": 30,
    "api_update_frequency_seconds": 300,  # 5 minutes
    "max_pagination_limit": 250,
    "seconds_per_month": 2592000,
    "seconds_per_year": 31536000,
}

# ============================================================================
# STRATEGY 1: COLLECT ALL COINS DAILY (SNAPSHOT APPROACH)
# ============================================================================

def analyze_daily_snapshot_all_coins():
    """
    Strategy: Collect all 13,532 coins' current market cap once per day
    - Simple pagination through /tickers endpoint
    - Store daily snapshots in JSONL format
    - No API restriction violations
    """
    print("=" * 80)
    print("STRATEGY 1: DAILY SNAPSHOT - Collect Current Market Cap for ALL Coins")
    print("=" * 80)

    total_coins = CONSTRAINTS["total_coins"]
    max_per_request = CONSTRAINTS["max_pagination_limit"]
    calls_needed_per_day = math.ceil(total_coins / max_per_request)
    calls_per_month = calls_needed_per_day * 30
    calls_per_year = calls_needed_per_day * 365

    print(f"\nBasic Metrics:")
    print(f"  Total coins: {total_coins:,}")
    print(f"  Max results per request: {max_per_request}")
    print(f"  API requests needed per day: {calls_needed_per_day}")
    print(f"  API requests needed per month: {calls_per_month:,}")
    print(f"  API requests needed per year: {calls_per_year:,}")

    # Rate limit analysis
    free_monthly = CONSTRAINTS["free_tier_calls_per_month"]
    daily_headroom = CONSTRAINTS["free_tier_calls_per_day"] - calls_needed_per_day

    print(f"\nFree Tier Rate Limit Analysis:")
    print(f"  Free tier monthly budget: {free_monthly:,}")
    print(f"  Monthly usage: {calls_per_month:,}")
    print(f"  Remaining for other ops: {free_monthly - calls_per_month:,}")
    print(f"  Daily budget: {CONSTRAINTS['free_tier_calls_per_day']}")
    print(f"  Daily snapshot usage: {calls_needed_per_day}")
    print(f"  Daily headroom: {daily_headroom}")
    print(f"  ✓ FITS IN FREE TIER: {calls_per_month <= free_monthly}")

    # Storage calculations
    avg_coin_data_bytes = 200  # Typical coin record in JSON
    daily_storage_bytes = total_coins * avg_coin_data_bytes
    daily_storage_mb = daily_storage_bytes / (1024 * 1024)
    monthly_storage_gb = (daily_storage_bytes * 30) / (1024**3)
    yearly_storage_gb = (daily_storage_bytes * 365) / (1024**3)

    print(f"\nStorage Calculations:")
    print(f"  Avg JSON per coin: ~{avg_coin_data_bytes} bytes")
    print(f"  Daily snapshot size: ~{daily_storage_mb:.2f} MB")
    print(f"  Monthly storage: ~{monthly_storage_gb:.2f} GB")
    print(f"  Yearly storage: ~{yearly_storage_gb:.2f} GB")

    # Time to historical coverage
    print(f"\nHistorical Coverage Timeline:")
    for years in [1, 2, 3, 5, 10]:
        storage_needed = yearly_storage_gb * years
        print(f"  {years}-year history: ~{storage_needed:.1f} GB")

    # Feasibility
    print(f"\n✓ FEASIBILITY ASSESSMENT:")
    print(f"  - Fits within free tier: YES")
    print(f"  - Storage manageable: YES")
    print(f"  - Can start immediately: YES")
    print(f"  - Implementation complexity: LOW")
    print(f"  - Risk level: LOW")

    return {
        "strategy": "daily_snapshot_all_coins",
        "calls_per_day": calls_needed_per_day,
        "calls_per_month": calls_per_month,
        "calls_per_year": calls_per_year,
        "fits_free_tier": calls_per_month <= free_monthly,
        "daily_storage_mb": daily_storage_mb,
        "monthly_storage_gb": monthly_storage_gb,
        "yearly_storage_gb": yearly_storage_gb,
    }

# ============================================================================
# STRATEGY 2: STRATIFIED SAMPLING (GRADUATED FREQUENCY)
# ============================================================================

def analyze_stratified_sampling():
    """
    Strategy: Different collection frequency based on market cap rank
    - Top 100 coins: 4x daily (every 6 hours)
    - Top 500 coins: 2x daily (every 12 hours)
    - Remaining 13,032: 1x daily (once per day)
    """
    print("\n" + "=" * 80)
    print("STRATEGY 2: STRATIFIED SAMPLING - Frequency Based on Rank")
    print("=" * 80)

    # Tier 1: Top 100 coins, 4x daily
    tier1_coins = 100
    tier1_requests_per_day = 4 * math.ceil(tier1_coins / CONSTRAINTS["max_pagination_limit"])

    # Tier 2: Top 500 coins, 2x daily
    tier2_coins = 400  # 500 - 100
    tier2_requests_per_day = 2 * math.ceil(tier2_coins / CONSTRAINTS["max_pagination_limit"])

    # Tier 3: Remaining coins, 1x daily
    tier3_coins = CONSTRAINTS["total_coins"] - 500
    tier3_requests_per_day = 1 * math.ceil(tier3_coins / CONSTRAINTS["max_pagination_limit"])

    total_daily = tier1_requests_per_day + tier2_requests_per_day + tier3_requests_per_day
    monthly = total_daily * 30
    yearly = total_daily * 365

    print(f"\nTier Breakdown:")
    print(f"  Tier 1 (Top 100): {tier1_coins:,} coins, {tier1_requests_per_day} requests/day")
    print(f"  Tier 2 (100-500): {tier2_coins:,} coins, {tier2_requests_per_day} requests/day")
    print(f"  Tier 3 (500+): {tier3_coins:,} coins, {tier3_requests_per_day} requests/day")
    print(f"  Total daily requests: {total_daily}")
    print(f"  Monthly requests: {monthly:,}")
    print(f"  Yearly requests: {yearly:,}")

    free_tier = CONSTRAINTS["free_tier_calls_per_month"]
    fits_free = monthly <= free_tier

    print(f"\nRate Limit Check:")
    print(f"  Free tier monthly budget: {free_tier:,}")
    print(f"  Strategy monthly usage: {monthly:,}")
    print(f"  ✓ Fits in free tier: {fits_free}")
    if not fits_free:
        deficit = monthly - free_tier
        print(f"  ✗ Exceeds by: {deficit:,} calls/month")

    # Storage is same as Strategy 1 (all coins collected daily)
    avg_coin_data_bytes = 200
    daily_storage_bytes = CONSTRAINTS["total_coins"] * avg_coin_data_bytes
    monthly_storage_gb = (daily_storage_bytes * 30) / (1024**3)
    yearly_storage_gb = (daily_storage_bytes * 365) / (1024**3)

    print(f"\nBenefits:")
    print(f"  - Finer granularity for volatile top coins")
    print(f"  - Better trend detection for top assets")
    print(f"  - Still fits free tier")
    print(f"  - Same yearly storage: ~{yearly_storage_gb:.2f} GB")

    return {
        "strategy": "stratified_sampling",
        "calls_per_day": total_daily,
        "calls_per_month": monthly,
        "calls_per_year": yearly,
        "fits_free_tier": fits_free,
        "monthly_storage_gb": monthly_storage_gb,
        "yearly_storage_gb": yearly_storage_gb,
    }

# ============================================================================
# STRATEGY 3: HISTORICAL BACKFILL WITH PAID TIER
# ============================================================================

def analyze_paid_tier_strategy():
    """
    Strategy: Use Starter ($30-50/month) tier to backfill historical data
    - 400,000 calls/month (Starter tier)
    - 30-day historical access
    - Collect all coins' last 30 days of daily data
    """
    print("\n" + "=" * 80)
    print("STRATEGY 3: PAID TIER BACKFILL - Starter Plan ($30-50/month)")
    print("=" * 80)

    starter_monthly_calls = 400000
    coins = CONSTRAINTS["total_coins"]

    # Backfill: Get last 30 days for each coin (using /ohlcv/historical or daily snapshots)
    # But free tier only allows 24h, so we need to use other approaches
    # Option A: Collect 30 daily snapshots (realistic approach)
    # Each snapshot: ceil(13532/250) = 55 requests

    daily_snapshot_requests = math.ceil(coins / CONSTRAINTS["max_pagination_limit"])
    backfill_days = 30
    backfill_snapshot_requests = daily_snapshot_requests * backfill_days

    print(f"\nBackfill Approach (30-day catch-up):")
    print(f"  Coins to backfill: {coins:,}")
    print(f"  Requests per daily snapshot: {daily_snapshot_requests}")
    print(f"  Days to backfill: {backfill_days}")
    print(f"  Total backfill requests: {backfill_snapshot_requests:,}")
    print(f"  Starter tier monthly budget: {starter_monthly_calls:,}")
    print(f"  Remaining for ongoing collection: {starter_monthly_calls - backfill_snapshot_requests:,}")
    print(f"  ✓ Backfill feasible: {backfill_snapshot_requests <= starter_monthly_calls}")

    # Ongoing collection after backfill
    ongoing_daily = daily_snapshot_requests
    ongoing_monthly = ongoing_daily * 30
    ongoing_yearly = ongoing_daily * 365

    print(f"\nOngoing Collection (after backfill):")
    print(f"  Daily requests: {ongoing_daily}")
    print(f"  Monthly requests: {ongoing_monthly:,}")
    print(f"  Yearly requests: {ongoing_yearly:,}")
    print(f"  All fit in Starter tier: YES")

    # Cost analysis
    starter_cost_monthly = 40  # Mid-range estimate
    cost_per_year = starter_cost_monthly * 12
    cost_per_10_years = cost_per_year * 10

    storage_per_year = (coins * 200 * 365) / (1024**3)

    print(f"\nCost Analysis (Starter Plan):")
    print(f"  Monthly subscription: ~${starter_cost_monthly}")
    print(f"  Annual cost: ~${cost_per_year}")
    print(f"  10-year cost: ~${cost_per_10_years}")
    print(f"  Storage needed per year: ~{storage_per_year:.2f} GB")
    print(f"  10-year storage: ~{storage_per_year * 10:.1f} GB")

    return {
        "strategy": "paid_starter_plan",
        "starter_monthly_budget": starter_monthly_calls,
        "backfill_requests": backfill_snapshot_requests,
        "ongoing_daily_requests": ongoing_daily,
        "ongoing_monthly_requests": ongoing_monthly,
        "ongoing_yearly_requests": ongoing_yearly,
        "monthly_cost_usd": starter_cost_monthly,
        "yearly_cost_usd": cost_per_year,
        "10year_cost_usd": cost_per_10_years,
        "storage_per_year_gb": storage_per_year,
    }

# ============================================================================
# STRATEGY 4: HYBRID - FREE ONGOING + PAID BACKFILL
# ============================================================================

def analyze_hybrid_strategy():
    """
    Strategy: Use free tier for ongoing daily collection + paid tier for backfill only
    - Free tier: Daily snapshots of all coins (sustainable)
    - Starter tier (month 1 only): Backfill 30 days of history
    - Cost: $40 one-time + $0 thereafter (switch to free)
    """
    print("\n" + "=" * 80)
    print("STRATEGY 4: HYBRID - Free Ongoing + One-time Paid Backfill")
    print("=" * 80)

    coins = CONSTRAINTS["total_coins"]
    daily_snapshot_requests = math.ceil(coins / CONSTRAINTS["max_pagination_limit"])

    # Month 1: Use Starter tier for backfill + ongoing
    backfill_days = 30
    backfill_requests = daily_snapshot_requests * backfill_days
    month1_total = backfill_requests + (daily_snapshot_requests * 1)

    # Month 2+: Free tier only
    free_monthly = CONSTRAINTS["free_tier_calls_per_month"]
    ongoing_monthly = daily_snapshot_requests * 30

    print(f"\nMonth 1: Starter Plan Backfill + Ongoing")
    print(f"  Backfill (30 days): {backfill_requests:,} requests")
    print(f"  Ongoing (1 month): {daily_snapshot_requests * 30:,} requests")
    print(f"  Month 1 total: {month1_total:,} requests")
    print(f"  Starter tier budget: 400,000")
    print(f"  ✓ Fits in one month: {month1_total <= 400000}")
    print(f"  Cost: ~$40")

    print(f"\nMonth 2+: Free Tier Only")
    print(f"  Daily snapshot requests: {daily_snapshot_requests}")
    print(f"  Monthly requests: {ongoing_monthly:,}")
    print(f"  Free tier monthly budget: {free_monthly:,}")
    print(f"  Remaining budget: {free_monthly - ongoing_monthly:,}")
    print(f"  ✓ Sustainable on free tier: YES")

    print(f"\nCost Analysis:")
    print(f"  One-time cost (Month 1): ~$40")
    print(f"  Ongoing cost: $0")
    print(f"  10-year cost: ~$40 (one-time only)")

    years_of_history = 10
    storage_per_year = (coins * 200 * 365) / (1024**3)
    total_storage = storage_per_year * years_of_history

    print(f"\nStorage for 10 years of daily snapshots:")
    print(f"  Per year: ~{storage_per_year:.2f} GB")
    print(f"  10 years: ~{total_storage:.1f} GB")

    print(f"\nBreakdown Timeline:")
    print(f"  Day 1: Start backfill on Starter plan")
    print(f"  Day 30: Complete 30-day backfill")
    print(f"  Day 31: Downgrade to free tier")
    print(f"  Day 31+: Daily collections forever on free tier")

    return {
        "strategy": "hybrid_free_plus_backfill",
        "month1_requests": month1_total,
        "ongoing_monthly_requests": ongoing_monthly,
        "one_time_cost_usd": 40,
        "ongoing_cost_monthly_usd": 0,
        "storage_per_year_gb": storage_per_year,
        "10year_storage_gb": total_storage,
        "feasible": ongoing_monthly <= free_monthly,
    }

# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    results = {}

    # Run all strategies
    results["strategy1"] = analyze_daily_snapshot_all_coins()
    results["strategy2"] = analyze_stratified_sampling()
    results["strategy3"] = analyze_paid_tier_strategy()
    results["strategy4"] = analyze_hybrid_strategy()

    # Save results
    with open("/tmp/historical-marketcap-all-coins/feasibility_calculations.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("FEASIBILITY CALCULATIONS SAVED")
    print("=" * 80)
    print("File: /tmp/historical-marketcap-all-coins/feasibility_calculations.json")
