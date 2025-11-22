#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""
Fetch ALL coin IDs from CoinGecko (active coins only - inactive requires paid plan)

Output: JSON file with all ~19,000+ coin IDs
"""

import json
import os
import sys
import time

import requests

# Use API key if available
api_key = os.getenv('COINGECKO_API_KEY')

url = "https://api.coingecko.com/api/v3/coins/list"
params = {'include_platform': 'false'}

if api_key:
    params['x_cg_demo_api_key'] = api_key
    print(f"✅ Using Demo API key")
else:
    print("⚠️  No API key (using free tier)")
    time.sleep(60)  # Wait to avoid rate limit

print(f"Fetching all active coins from CoinGecko...")

response = requests.get(url, params=params, timeout=30)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
    sys.exit(1)

coins = response.json()

print(f"✅ Retrieved {len(coins):,} active coins")

# Save to file
output_file = 'data/coingecko_all_coin_ids.json'
with open(output_file, 'w') as f:
    json.dump(coins, f, indent=2)

print(f"✅ Saved to: {output_file}")

# Show sample
print(f"\nSample coins:")
for coin in coins[:10]:
    print(f"  {coin['id']:30s} {coin['symbol']:10s} {coin['name']}")

# Look for old/dead coins
print(f"\nSearching for historically important dead coins...")
targets = ['namecoin', 'peercoin', 'terracoin', 'novacoin', 'feathercoin']
found = [c for c in coins if c['id'] in targets]

if found:
    print("✅ Found in 'active' list:")
    for coin in found:
        print(f"  {coin['id']:30s} {coin['symbol']:10s} {coin['name']}")
else:
    print("❌ None found - might be in 'inactive' list (paid only)")

print(f"\n📊 Summary:")
print(f"  Total active coins: {len(coins):,}")
print(f"  Output file: {output_file}")
