#!/usr/bin/env python3
"""
Endpoint Analysis: Available Methods for Collecting All Coins' Market Cap
=========================================================================

Analyzes which endpoints can practically be used for collecting historical
market cap data across all 13,532 coins.
"""

import json
from datetime import datetime

ANALYSIS = {
    "date_analyzed": datetime.now().isoformat(),
    "total_coins": 13532,
    "endpoints": {}
}

# ============================================================================
# ENDPOINT 1: /v1/tickers - CURRENT MARKET CAP FOR ALL COINS
# ============================================================================

ANALYSIS["endpoints"]["/v1/tickers"] = {
    "name": "Get All Tickers",
    "method": "GET",
    "url": "https://api.coinpaprika.com/v1/tickers",
    "description": "Returns current market cap, price, volume for all coins",
    "primary_market_cap_field": "quotes.USD.market_cap",
    "response_type": "Array of coin objects",
    "pagination": {
        "method": "limit/offset",
        "max_limit": 250,
        "default_limit": 50,
        "offset_parameter": "offset"
    },
    "to_get_all_coins": {
        "requests_needed": 54,  # ceil(13532/250)
        "calculation": "13532 / 250 = 54.128 → 55 requests",
        "actual": 55
    },
    "data_freshness": "Real-time (updated every 5 minutes)",
    "free_tier_access": True,
    "historical_depth_free": "Real-time snapshot only",
    "use_cases": [
        "Daily snapshots of all coins",
        "Rank-based collections",
        "Trend detection",
        "Market cap tracking"
    ],
    "limitations": [
        "Only current data, no historical lookback",
        "Must store snapshots to build history"
    ],
    "rate_limit_cost": {
        "per_call": 1,
        "per_all_coins": 55,
        "per_day_safe": "55 calls/day with 595 calls remaining"
    },
    "data_volume": {
        "bytes_per_coin": 200,
        "daily_mb": 2.58,
        "monthly_gb": 0.08,
        "yearly_gb": 0.92
    },
    "recommended": True,
    "recommendation_reason": "Most efficient way to collect all coins' current market cap"
}

# ============================================================================
# ENDPOINT 2: /v1/global - AGGREGATE MARKET CAP
# ============================================================================

ANALYSIS["endpoints"]["/v1/global"] = {
    "name": "Get Global Market Data",
    "method": "GET",
    "url": "https://api.coinpaprika.com/v1/global",
    "description": "Returns total crypto market cap and aggregate statistics",
    "primary_market_cap_field": "market_cap_usd",
    "response_type": "Single JSON object",
    "data_returned": {
        "market_cap_usd": "Total market capitalization",
        "market_cap_change_24h": "24-hour change percentage",
        "bitcoin_dominance_percentage": "BTC's share of market",
        "cryptocurrencies_number": "Total coins tracked",
        "volume_24h_usd": "Total 24h trading volume"
    },
    "free_tier_access": True,
    "historical_depth_free": "Real-time snapshot only",
    "pagination": "Not applicable (single response)",
    "use_cases": [
        "Track total market cap trends",
        "Monitor Bitcoin dominance",
        "Market-wide volatility",
        "Aggregate statistics"
    ],
    "rate_limit_cost": {
        "per_call": 1,
        "per_day": "Can call multiple times per day"
    },
    "data_volume": {
        "bytes_per_call": 500,
        "daily_kb": 0.5,
        "monthly_mb": 0.015,
        "yearly_mb": 0.18
    },
    "recommended": True,
    "recommendation_reason": "Cheap to collect, provides market-wide context"
}

# ============================================================================
# ENDPOINT 3: /v1/coins/{id}/ohlcv/today - TODAY'S OHLCV
# ============================================================================

ANALYSIS["endpoints"]["/v1/coins/{id}/ohlcv/today"] = {
    "name": "Get Coin OHLCV for Today",
    "method": "GET",
    "url": "https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/today",
    "description": "Today's open/high/low/close prices with market cap",
    "primary_market_cap_field": "market_cap",
    "data_fields": ["time_open", "time_close", "open", "high", "low", "close", "volume", "market_cap"],
    "free_tier_access": True,
    "historical_depth_free": "Current day only",
    "to_get_all_coins": {
        "requests_needed": 13532,
        "calculation": "One request per coin"
    },
    "rate_limit_cost": {
        "per_call": 1,
        "per_all_coins": 13532,
        "exceeds_free_monthly": "20 times over (13,532 vs 20,000 monthly budget)"
    },
    "feasibility": "NOT FEASIBLE",
    "feasibility_reason": "Would require 13,532 API calls for all coins, exceeds free tier dramatically",
    "use_cases": [
        "Detailed price movement data",
        "Daily OHLCV tracking"
    ],
    "limitations": [
        "One API call per coin",
        "Exceeds free tier monthly budget by 20x",
        "Cannot use for daily updates of all coins"
    ],
    "recommended": False,
    "recommendation_reason": "Inefficient compared to /v1/tickers endpoint which provides same data"
}

# ============================================================================
# ENDPOINT 4: /v1/coins/{id}/ohlcv/latest - YESTERDAY'S OHLCV
# ============================================================================

ANALYSIS["endpoints"]["/v1/coins/{id}/ohlcv/latest"] = {
    "name": "Get Coin OHLCV for Latest Complete Day",
    "method": "GET",
    "url": "https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/latest",
    "description": "Previous full 24-hour period's OHLCV and market cap",
    "primary_market_cap_field": "market_cap",
    "free_tier_access": True,
    "historical_depth_free": "Previous 24-hour period only",
    "to_get_all_coins": {
        "requests_needed": 13532,
        "exceeds_free_monthly": True
    },
    "feasibility": "NOT FEASIBLE",
    "feasibility_reason": "Same limitation as /ohlcv/today - one call per coin",
    "recommended": False
}

# ============================================================================
# ENDPOINT 5: /v1/coins/{id}/ohlcv/historical - HISTORICAL OHLCV
# ============================================================================

ANALYSIS["endpoints"]["/v1/coins/{id}/ohlcv/historical"] = {
    "name": "Get Historical OHLCV Data",
    "method": "GET",
    "url": "https://api.coinpaprika.com/v1/coins/{coin_id}/ohlcv/historical",
    "description": "Historical open/high/low/close with market cap for date range",
    "primary_market_cap_field": "market_cap",
    "parameters": {
        "start": "Start date (YYYY-MM-DD)",
        "end": "End date (YYYY-MM-DD)",
        "interval": "Time interval (5m, 15m, 30m, 1h, 6h, 12h, 24h)"
    },
    "free_tier_access": True,
    "free_tier_limitations": {
        "max_historical_range": "24 hours only",
        "available_intervals": "24h only",
        "error_code": 402,
        "error_message": "Getting historical OHLCV data before [timestamp] is not allowed in this plan"
    },
    "paid_tier_access": {
        "Starter ($30-50/mo)": {
            "max_range": "30 days",
            "intervals": "24h only"
        },
        "Pro ($100+/mo)": {
            "max_range": "90 days",
            "intervals": "24h only"
        },
        "Business ($300+/mo)": {
            "max_range": "365 days",
            "intervals": "1h, 6h, 12h, 24h"
        },
        "Enterprise": {
            "max_range": "Unlimited",
            "intervals": "5m, 15m, 30m, 1h, 6h, 12h, 24h"
        }
    },
    "to_backfill_30_days": {
        "coins": 13532,
        "requests_per_coin": 1,  # One request per coin for 30-day range
        "total_requests": 13532,
        "feasibility_free": False,
        "feasibility_starter": True
    },
    "feasibility": "Limited on free, good on paid",
    "recommended_for_backfill": True,
    "recommendation_reason": "Best endpoint for getting historical ranges, but requires paid tier",
    "limitations": [
        "Free tier: 24 hours only",
        "Requires paid tier for historical depth",
        "One request per coin per date range"
    ],
    "use_cases": [
        "Backfilling historical data",
        "Getting date-range summaries",
        "Historical trend analysis"
    ]
}

# ============================================================================
# ENDPOINT 6: /v1/tickers/{id}/historical - TICKER HISTORY
# ============================================================================

ANALYSIS["endpoints"]["/v1/tickers/{id}/historical"] = {
    "name": "Get Ticker Historical Data",
    "method": "GET",
    "url": "https://api.coinpaprika.com/v1/tickers/{coin_id}/historical",
    "description": "Historical price, volume, and market cap for a coin",
    "primary_market_cap_field": "quotes.USD.market_cap",
    "free_tier_access": True,
    "free_tier_limitations": {
        "error_code": 402,
        "error_message": "Getting minute historical data is not allowed in this plan",
        "note": "Free tier may have access to daily historical data"
    },
    "to_get_all_coins_1_year": {
        "coins": 13532,
        "requests_per_coin": 1,  # One request for full year daily data
        "total_requests": 13532,
        "exceeds_free_monthly": True
    },
    "feasibility": "Limited - likely requires paid tier",
    "recommended": False,
    "recommendation_reason": "Requires paid tier for daily data beyond limited period"
}

# ============================================================================
# STRATEGY RECOMMENDATIONS
# ============================================================================

ANALYSIS["recommended_strategies"] = {
    "RECOMMENDED": {
        "strategy": "Daily Snapshot Using /v1/tickers",
        "description": "Collect all coins' current market cap once per day using paginated /v1/tickers endpoint",
        "implementation": {
            "frequency": "Once per day",
            "endpoint": "/v1/tickers",
            "pagination": "Loop through with limit=250, offset=0,250,500,...,13250",
            "total_requests_per_day": 55,
            "storage": "JSONL format with timestamp"
        },
        "rate_limits": {
            "free_tier_monthly": 20000,
            "strategy_monthly": 1650,
            "headroom": 18350,
            "feasible": True
        },
        "storage_requirements": {
            "daily": "2.58 MB",
            "monthly": "77 MB",
            "yearly": "0.92 GB",
            "10_years": "9.2 GB"
        },
        "cost": "Free forever",
        "advantages": [
            "Fits easily within free tier",
            "Minimal storage",
            "Can maintain indefinitely",
            "Simple implementation",
            "Low risk"
        ],
        "disadvantages": [
            "Only current market cap, no historical lookback",
            "Must collect daily to build history",
            "Cannot backfill old data on free tier"
        ],
        "timeline": {
            "immediate": "Start collecting today",
            "1_month": "30 daily snapshots",
            "6_months": "180 daily snapshots",
            "1_year": "365 daily snapshots"
        }
    },
    "OPTIONAL_ENHANCEMENT_1": {
        "strategy": "Hybrid: One-time Paid Backfill + Free Ongoing",
        "description": "Use Starter tier for one month to backfill 30 days of history, then switch to free forever",
        "month_1_cost": "$40",
        "month_2_onwards_cost": "$0",
        "10_year_cost": "$40",
        "implementation": {
            "month_1": "Use Starter tier to collect all coins' data for past 30 days",
            "month_2_onwards": "Downgrade to free tier, continue daily collection"
        },
        "achieves": "30-day historical baseline + indefinite ongoing collection",
        "advantages": [
            "Minimal cost",
            "Instant 30-day history in month 1",
            "Free ongoing collection forever"
        ]
    },
    "OPTIONAL_ENHANCEMENT_2": {
        "strategy": "Stratified Sampling by Rank",
        "description": "Collect top 100 coins 4x daily, top 500 coins 2x daily, rest once daily",
        "requests_per_day": 61,
        "monthly_requests": 1830,
        "feasible": True,
        "advantages": [
            "Better granularity for volatile top coins",
            "Still fits free tier",
            "Captures price swings in major assets"
        ]
    }
}

# ============================================================================
# ENDPOINT COMPARISON TABLE
# ============================================================================

ANALYSIS["endpoint_comparison_table"] = [
    {
        "endpoint": "/v1/tickers",
        "method": "GET all coins",
        "calls_for_all_coins": 55,
        "free_tier": "YES",
        "monthly_cost": "$0",
        "recommended": "YES",
        "reason": "Most efficient"
    },
    {
        "endpoint": "/v1/global",
        "method": "GET global stats",
        "calls_for_all_coins": 1,
        "free_tier": "YES",
        "monthly_cost": "$0",
        "recommended": "YES",
        "reason": "Complements individual coins"
    },
    {
        "endpoint": "/v1/coins/{id}/ohlcv/today",
        "method": "Get each coin today",
        "calls_for_all_coins": 13532,
        "free_tier": "YES",
        "monthly_cost": "$0",
        "recommended": "NO",
        "reason": "Exceeds free tier 20x"
    },
    {
        "endpoint": "/v1/coins/{id}/ohlcv/latest",
        "method": "Get each coin yesterday",
        "calls_for_all_coins": 13532,
        "free_tier": "YES",
        "monthly_cost": "$0",
        "recommended": "NO",
        "reason": "Exceeds free tier 20x"
    },
    {
        "endpoint": "/v1/coins/{id}/ohlcv/historical",
        "method": "Get historical range",
        "calls_for_all_coins": 13532,
        "free_tier": "24h only",
        "monthly_cost": "$40+ for backfill",
        "recommended": "For backfill only",
        "reason": "Requires paid tier"
    },
    {
        "endpoint": "/v1/tickers/{id}/historical",
        "method": "Get ticker history",
        "calls_for_all_coins": 13532,
        "free_tier": "Limited",
        "monthly_cost": "$40+ for data",
        "recommended": "NO",
        "reason": "Requires paid tier"
    }
]

if __name__ == "__main__":
    with open("/tmp/historical-marketcap-all-coins/endpoint_analysis.json", "w") as f:
        json.dump(ANALYSIS, f, indent=2)

    print("ENDPOINT ANALYSIS SUMMARY")
    print("=" * 80)
    print("\nRECOMMENDED STRATEGY:")
    print("Use /v1/tickers endpoint with pagination to collect all coins once daily")
    print(f"  - API Calls: 55 per day (fits easily in 650/day free tier)")
    print(f"  - Monthly Cost: $0")
    print(f"  - Storage: 0.92 GB per year")
    print(f"  - Feasibility: 100% (immediate implementation)")

    print("\nOPTIONAL: One-time $40 Starter Plan for 30-day backfill in Month 1")
    print("Then switch to free tier for indefinite daily collection")
    print(f"  - 10-year cost: $40 one-time only")
    print(f"  - Starting history: 30 days of past data + ongoing daily")

    print("\n" + "=" * 80)
    print("Detailed analysis saved to: endpoint_analysis.json")
