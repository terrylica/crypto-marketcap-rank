#!/usr/bin/env python3
"""
PEP 723 Storage Requirements Analysis
Analyzes storage for historical market cap data across all coins
"""
# /// script
# dependencies = [
#   "python-json-benchmark==0.1.1",
#   "orjson==3.9.10",
# ]
# ///

import json
import sys
from pathlib import Path
from typing import Dict, Any
import struct

def analyze_jsonl_record():
    """Analyze a single market cap record"""
    # Sample market cap record (simplified)
    record = {
        "_collected_at": "2025-11-20T01:46:25.030820",
        "id": "btc-bitcoin",
        "rank": 1,
        "price": 92475.69527602357,
        "market_cap": 1844993878487,
        "volume_24h": 70498391995.82582,
        "market_cap_change_24h": -0.19,
        "percent_change_24h": -0.19,
        "percent_change_7d": -9.56,
        "percent_change_30d": -15.02,
        "timestamp": "2025-11-20T01:44:29Z"
    }
    
    # Estimate sizes
    json_str = json.dumps(record)
    raw_size = len(json_str.encode('utf-8'))
    
    print("=" * 70)
    print("SINGLE MARKET CAP RECORD ANALYSIS")
    print("=" * 70)
    print(f"Raw JSON size: {raw_size:,} bytes")
    print(f"JSON content:\n{json.dumps(record, indent=2)}\n")
    
    return raw_size

def calculate_storage_requirements():
    """Calculate storage requirements for all coins"""
    print("\n" + "=" * 70)
    print("STORAGE REQUIREMENT CALCULATIONS")
    print("=" * 70)
    
    num_coins = 13532
    record_size_bytes = 350  # Average JSON record size
    
    # Daily collection scenario
    daily_records_per_year = 365
    yearly_growth_scenarios = {
        "1 sample/day (minimal)": 1,
        "4 samples/day (6-hourly)": 4,
        "24 samples/day (hourly)": 24,
    }
    
    print(f"\nAssumptions:")
    print(f"  - Total coins: {num_coins:,}")
    print(f"  - Avg record size: {record_size_bytes} bytes")
    print(f"  - Days per year: 365")
    
    print(f"\n{'Sampling Frequency':<30} {'Year 1':<15} {'5 Years':<15} {'10 Years':<15}")
    print("-" * 60)
    
    results = {}
    for scenario, samples_per_day in yearly_growth_scenarios.items():
        year1_records = num_coins * daily_records_per_year * samples_per_day
        year1_bytes = year1_records * record_size_bytes
        year1_gb = year1_bytes / (1024**3)
        
        year5_bytes = year1_bytes * 5
        year5_gb = year5_bytes / (1024**3)
        
        year10_bytes = year1_bytes * 10
        year10_gb = year10_bytes / (1024**3)
        
        results[scenario] = {
            "year1_gb": year1_gb,
            "year5_gb": year5_gb,
            "year10_gb": year10_gb,
            "year1_records": year1_records
        }
        
        print(f"{scenario:<30} {year1_gb:>6.1f} GB       {year5_gb:>6.1f} GB       {year10_gb:>6.1f} GB")
    
    return results

def estimate_compression_ratios():
    """Estimate compression ratios for different formats"""
    print("\n" + "=" * 70)
    print("COMPRESSION RATIO ANALYSIS")
    print("=" * 70)
    
    original_size_mb = 42 * 1024  # 42GB base scenario
    
    compression_formats = {
        "JSONL (uncompressed)": 1.0,
        "JSONL + gzip": 0.25,
        "JSONL + brotli": 0.20,
        "Parquet (snappy)": 0.30,
        "Parquet (brotli)": 0.15,
        "MessagePack + gzip": 0.22,
        "Protocol Buffers + gzip": 0.18,
    }
    
    print(f"\nBase storage: {original_size_mb/1024:.1f} GB/year (42GB scenario)")
    print(f"\n{'Format':<30} {'Compression Ratio':<20} {'Size (GB)':<15}")
    print("-" * 65)
    
    results = {}
    for fmt, ratio in compression_formats.items():
        compressed_mb = original_size_mb * ratio
        compressed_gb = compressed_mb / 1024
        results[fmt] = compressed_gb
        print(f"{fmt:<30} {ratio:.2%}           {compressed_gb:>6.2f} GB")
    
    return results

def storage_cost_analysis():
    """Analyze storage costs for different tiers"""
    print("\n" + "=" * 70)
    print("STORAGE COST ANALYSIS (Annual)")
    print("=" * 70)
    
    storage_tiers = {
        "Local SSD ($/GB/year)": 0.12,
        "AWS S3 Standard ($/GB/year)": 0.023,
        "AWS S3 Glacier ($/GB/year)": 0.004,
        "Database (SQLite local)": "free",
    }
    
    year1_gb = 42.0  # Base scenario
    year5_gb = 42.0 * 5
    year10_gb = 42.0 * 10
    
    print(f"\nBase scenario: 42 GB/year (all 13,532 coins, hourly samples)")
    print(f"\n{'Storage Tier':<35} {'Year 1':<15} {'Year 5':<15} {'Year 10':<15}")
    print("-" * 65)
    
    for tier, cost in storage_tiers.items():
        if cost == "free":
            print(f"{tier:<35} {'Free':<15} {'Free':<15} {'Free':<15}")
        else:
            y1_cost = year1_gb * cost
            y5_cost = year5_gb * cost
            y10_cost = year10_gb * cost
            print(f"{tier:<35} ${y1_cost:>6.2f}      ${y5_cost:>7.2f}      ${y10_cost:>8.2f}")
    
    return {
        "year1_gb": year1_gb,
        "year5_gb": year5_gb,
        "year10_gb": year10_gb,
    }

def recommend_storage_format():
    """Recommend optimal storage format"""
    print("\n" + "=" * 70)
    print("STORAGE FORMAT RECOMMENDATIONS")
    print("=" * 70)
    
    formats = {
        "JSONL + gzip": {
            "pros": [
                "Human readable (raw)",
                "Simple streaming append",
                "Standard line-by-line processing",
                "Good compression (75% reduction)"
            ],
            "cons": [
                "Requires decompression for queries",
                "No indexing without rebuilding"
            ],
            "use_case": "Time-series logging, archival"
        },
        "SQLite + WAL": {
            "pros": [
                "ACID transactions",
                "Efficient queries with indexes",
                "Single file distribution",
                "Full-text search capable"
            ],
            "cons": [
                "Slightly larger than compressed JSONL",
                "Lock contention under heavy writes"
            ],
            "use_case": "Active querying, analytics"
        },
        "Parquet (columnar)": {
            "pros": [
                "Excellent compression (70%+ reduction)",
                "Optimized for analytical queries",
                "Language-agnostic format",
                "Predicate pushdown efficiency"
            ],
            "cons": [
                "Not ideal for streaming append",
                "Requires columnar data ingestion"
            ],
            "use_case": "Analytics, batch processing, archives"
        },
    }
    
    for fmt, details in formats.items():
        print(f"\n{fmt}")
        print("-" * 50)
        print("Pros:")
        for pro in details["pros"]:
            print(f"  + {pro}")
        print("Cons:")
        for con in details["cons"]:
            print(f"  - {con}")
        print(f"Best for: {details['use_case']}")

if __name__ == "__main__":
    analyze_jsonl_record()
    storage_reqs = calculate_storage_requirements()
    compression = estimate_compression_ratios()
    costs = storage_cost_analysis()
    recommend_storage_format()
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
