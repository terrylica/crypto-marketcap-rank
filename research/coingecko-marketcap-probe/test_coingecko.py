#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests",
# ]
# ///

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "https://api.coingecko.com/api/v3"

def test_market_chart(coin_id, days, label):
    """Test the market_chart endpoint for a specific coin and time range."""
    print(f"\n{'='*80}")
    print(f"Testing: {coin_id} - {label} (days={days})")
    print('='*80)
    
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days
    }
    
    try:
        start_time = time.time()
        response = requests.get(url, params=params)
        elapsed = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check what keys are present
            print(f"\nResponse Keys: {list(data.keys())}")
            
            # Analyze market_caps if present
            if 'market_caps' in data:
                market_caps = data['market_caps']
                print(f"\nMarket Caps Data Points: {len(market_caps)}")
                
                if market_caps:
                    # First data point
                    first_timestamp = market_caps[0][0] / 1000
                    first_date = datetime.fromtimestamp(first_timestamp)
                    first_value = market_caps[0][1]
                    
                    # Last data point
                    last_timestamp = market_caps[-1][0] / 1000
                    last_date = datetime.fromtimestamp(last_timestamp)
                    last_value = market_caps[-1][1]
                    
                    print(f"\nFirst Data Point:")
                    print(f"  Date: {first_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  Market Cap: ${first_value:,.2f}")
                    
                    print(f"\nLast Data Point:")
                    print(f"  Date: {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  Market Cap: ${last_value:,.2f}")
                    
                    # Calculate time span
                    days_span = (last_date - first_date).days
                    print(f"\nTime Span: {days_span} days ({days_span/365:.1f} years)")
                    
                    # Show first 3 and last 3 entries
                    print(f"\nFirst 3 entries (raw):")
                    for entry in market_caps[:3]:
                        ts = datetime.fromtimestamp(entry[0]/1000)
                        print(f"  {ts.strftime('%Y-%m-%d %H:%M:%S')}: ${entry[1]:,.2f}")
                    
                    print(f"\nLast 3 entries (raw):")
                    for entry in market_caps[-3:]:
                        ts = datetime.fromtimestamp(entry[0]/1000)
                        print(f"  {ts.strftime('%Y-%m-%d %H:%M:%S')}: ${entry[1]:,.2f}")
                    
                    return {
                        'success': True,
                        'coin': coin_id,
                        'days_requested': days,
                        'data_points': len(market_caps),
                        'first_date': first_date.strftime('%Y-%m-%d'),
                        'last_date': last_date.strftime('%Y-%m-%d'),
                        'days_span': days_span,
                        'has_market_cap': True
                    }
            else:
                print("\nWARNING: No 'market_caps' key in response!")
                return {
                    'success': True,
                    'coin': coin_id,
                    'days_requested': days,
                    'has_market_cap': False
                }
        else:
            print(f"\nError Response: {response.text}")
            return {
                'success': False,
                'coin': coin_id,
                'days_requested': days,
                'status_code': response.status_code
            }
            
    except Exception as e:
        print(f"\nException: {e}")
        return {
            'success': False,
            'coin': coin_id,
            'error': str(e)
        }

def test_coin_list():
    """Get list of available coins."""
    print(f"\n{'='*80}")
    print("Testing: Coin List Endpoint")
    print('='*80)
    
    url = f"{BASE_URL}/coins/list"
    response = requests.get(url)
    
    if response.status_code == 200:
        coins = response.json()
        print(f"Total coins available: {len(coins)}")
        print(f"\nFirst 10 coins:")
        for coin in coins[:10]:
            print(f"  {coin['id']}: {coin['name']} ({coin['symbol'].upper()})")
        return coins
    else:
        print(f"Error: {response.status_code}")
        return None

# Test suite
def run_tests():
    results = []
    
    # Test 1: Coin list
    print("\n" + "#"*80)
    print("# PHASE 1: Test Coin List")
    print("#"*80)
    test_coin_list()
    time.sleep(1)  # Rate limiting
    
    # Test 2: Bitcoin - Maximum history
    print("\n" + "#"*80)
    print("# PHASE 2: Bitcoin Historical Tests")
    print("#"*80)
    
    results.append(test_market_chart('bitcoin', '365', 'Bitcoin - 1 year'))
    time.sleep(1)
    
    results.append(test_market_chart('bitcoin', '730', 'Bitcoin - 2 years'))
    time.sleep(1)
    
    results.append(test_market_chart('bitcoin', '1825', 'Bitcoin - 5 years'))
    time.sleep(1)
    
    results.append(test_market_chart('bitcoin', 'max', 'Bitcoin - MAX history'))
    time.sleep(1)
    
    # Test 3: Ethereum
    print("\n" + "#"*80)
    print("# PHASE 3: Ethereum Historical Tests")
    print("#"*80)
    
    results.append(test_market_chart('ethereum', '365', 'Ethereum - 1 year'))
    time.sleep(1)
    
    results.append(test_market_chart('ethereum', 'max', 'Ethereum - MAX history'))
    time.sleep(1)
    
    # Test 4: Newer coins
    print("\n" + "#"*80)
    print("# PHASE 4: Newer Coins")
    print("#"*80)
    
    newer_coins = [
        ('solana', 'Solana (2020)'),
        ('cardano', 'Cardano (2017)'),
        ('polkadot', 'Polkadot (2020)'),
    ]
    
    for coin_id, label in newer_coins:
        results.append(test_market_chart(coin_id, 'max', label))
        time.sleep(1)
    
    # Test 5: Diverse sample
    print("\n" + "#"*80)
    print("# PHASE 5: Diverse Coin Sample")
    print("#"*80)
    
    diverse_coins = [
        ('ripple', 'XRP'),
        ('litecoin', 'Litecoin'),
        ('chainlink', 'Chainlink'),
        ('uniswap', 'Uniswap'),
        ('avalanche-2', 'Avalanche'),
    ]
    
    for coin_id, label in diverse_coins:
        results.append(test_market_chart(coin_id, 'max', label))
        time.sleep(1)
    
    # Summary
    print("\n" + "#"*80)
    print("# SUMMARY OF RESULTS")
    print("#"*80)
    
    print(f"\n{'Coin':<20} {'Days Req':<12} {'Days Span':<12} {'Data Points':<12} {'First Date':<15} {'Last Date':<15}")
    print("-" * 96)
    
    for result in results:
        if result.get('success') and result.get('has_market_cap'):
            print(f"{result['coin']:<20} {str(result['days_requested']):<12} {result['days_span']:<12} {result['data_points']:<12} {result['first_date']:<15} {result['last_date']:<15}")
    
    # Save results
    with open('/tmp/coingecko-marketcap-probe/test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: /tmp/coingecko-marketcap-probe/test_results.json")

if __name__ == "__main__":
    run_tests()
