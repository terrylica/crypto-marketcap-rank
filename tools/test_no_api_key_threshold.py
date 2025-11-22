#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///
"""
Test CoinGecko rate limit threshold WITHOUT API key

Purpose: Find the minimum delay needed to avoid 429 errors without registration

Usage:
    uv run tools/test_no_api_key_threshold.py --delay 10.0 --test-coins 20
"""

import argparse
import sys
import time
from datetime import datetime

import requests


def test_no_api_key_collection(delay_seconds: float, num_coins: int = 20):
    """
    Test collection without API key using specified delay.

    Args:
        delay_seconds: Seconds to wait between requests
        num_coins: Number of coins to test with

    Returns:
        dict: Results including success rate and errors
    """
    print(f"Testing NO-API-KEY collection")
    print(f"Delay: {delay_seconds}s between requests ({60/delay_seconds:.1f} calls/min)")
    print(f"Test coins: {num_coins}")
    print(f"Estimated time: {(num_coins * delay_seconds / 60):.1f} minutes")
    print()

    # Get top N coins
    print("Step 1: Getting coin list...")
    base_url = "https://api.coingecko.com/api/v3"

    try:
        response = requests.get(
            f"{base_url}/coins/markets",
            params={
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': num_coins,
                'page': 1,
                'sparkline': 'false'
            },
            timeout=30
        )

        if response.status_code != 200:
            print(f"❌ Failed to get coin list: {response.status_code}")
            return None

        coins = response.json()
        print(f"✅ Retrieved {len(coins)} coins")
        print()

    except Exception as e:
        print(f"❌ Error getting coin list: {e}")
        return None

    # Test collection
    print(f"Step 2: Testing collection (this will take {(num_coins * delay_seconds / 60):.1f} min)...")
    print()

    successes = 0
    failures = 0
    rate_limit_errors = 0
    other_errors = 0
    start_time = datetime.now()

    for idx, coin in enumerate(coins, 1):
        coin_id = coin['id']

        # Rate limiting
        if idx > 1:
            time.sleep(delay_seconds)

        try:
            response = requests.get(
                f"{base_url}/coins/{coin_id}/market_chart",
                params={
                    'vs_currency': 'usd',
                    'days': 365,
                    'interval': 'daily'
                },
                timeout=30
            )

            if response.status_code == 429:
                print(f"  [{idx}/{num_coins}] {coin_id:20s} ❌ RATE LIMIT (429)")
                failures += 1
                rate_limit_errors += 1
            elif response.status_code == 200:
                data = response.json()
                records = len(data.get('prices', []))
                print(f"  [{idx}/{num_coins}] {coin_id:20s} ✅ {records} records")
                successes += 1
            else:
                print(f"  [{idx}/{num_coins}] {coin_id:20s} ❌ Error {response.status_code}")
                failures += 1
                other_errors += 1

        except Exception as e:
            print(f"  [{idx}/{num_coins}] {coin_id:20s} ❌ Exception: {str(e)[:50]}")
            failures += 1
            other_errors += 1

    elapsed = (datetime.now() - start_time).total_seconds()

    print()
    print("="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Delay setting:       {delay_seconds}s ({60/delay_seconds:.1f} calls/min)")
    print(f"Coins tested:        {num_coins}")
    print(f"Successes:           {successes} ({100*successes/(successes+failures):.1f}%)")
    print(f"Failures:            {failures}")
    print(f"  - Rate limit (429): {rate_limit_errors}")
    print(f"  - Other errors:     {other_errors}")
    print(f"Actual time:         {elapsed/60:.1f} minutes")
    print()

    if successes == num_coins:
        print("✅ SUCCESS! This delay works without API key!")
        print(f"   Recommended: {delay_seconds}s delay for no-API-key usage")
        print(f"   For 500 coins: ~{500 * delay_seconds / 60:.1f} minutes ({500 * delay_seconds / 3600:.1f} hours)")
    elif successes > num_coins * 0.9:
        print("⚠️  MOSTLY WORKS - Some failures but >90% success")
        print(f"   Consider slightly increasing delay to {delay_seconds * 1.2:.1f}s")
    else:
        print("❌ TOO FAST - High failure rate")
        print(f"   Try again with delay >= {delay_seconds * 2:.1f}s")

    return {
        'delay': delay_seconds,
        'num_coins': num_coins,
        'successes': successes,
        'failures': failures,
        'rate_limit_errors': rate_limit_errors,
        'success_rate': successes / (successes + failures) if (successes + failures) > 0 else 0,
        'elapsed_minutes': elapsed / 60
    }


def main():
    parser = argparse.ArgumentParser(
        description='Test CoinGecko rate limit threshold without API key'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=10.0,
        help='Seconds to wait between requests (default: 10.0)'
    )
    parser.add_argument(
        '--test-coins',
        type=int,
        default=20,
        help='Number of coins to test with (default: 20)'
    )

    args = parser.parse_args()

    result = test_no_api_key_collection(args.delay, args.test_coins)

    if result and result['success_rate'] == 1.0:
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
