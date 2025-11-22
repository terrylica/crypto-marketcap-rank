#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests",
# ]
# ///

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://api.coingecko.com/api/v3"

def test_single_coin(coin_id, days='max'):
    """Test a single coin with market cap data."""
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {'vs_currency': 'usd', 'days': days}
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'market_caps' in data:
                mc = data['market_caps']
                if mc:
                    first_date = datetime.fromtimestamp(mc[0][0]/1000)
                    last_date = datetime.fromtimestamp(mc[-1][0]/1000)
                    days_span = (last_date - first_date).days
                    
                    return {
                        'coin': coin_id,
                        'success': True,
                        'data_points': len(mc),
                        'first_date': first_date.strftime('%Y-%m-%d'),
                        'last_date': last_date.strftime('%Y-%m-%d'),
                        'days_span': days_span,
                        'first_value': mc[0][1],
                        'last_value': mc[-1][1]
                    }
        elif response.status_code == 401:
            return {'coin': coin_id, 'success': False, 'error': '401 - Beyond 365 days limit'}
        elif response.status_code == 429:
            return {'coin': coin_id, 'success': False, 'error': '429 - Rate limited'}
        else:
            return {'coin': coin_id, 'success': False, 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'coin': coin_id, 'success': False, 'error': str(e)}

# Test with longer delays to avoid rate limits
coins_to_test = [
    ('bitcoin', 'Bitcoin (2009)'),
    ('ethereum', 'Ethereum (2015)'),
    ('litecoin', 'Litecoin (2011)'),
    ('ripple', 'XRP (2012)'),
    ('cardano', 'Cardano (2017)'),
    ('polkadot', 'Polkadot (2020)'),
    ('solana', 'Solana (2020)'),
    ('chainlink', 'Chainlink (2017)'),
    ('stellar', 'Stellar (2014)'),
    ('dogecoin', 'Dogecoin (2013)'),
]

results = []
print("Testing coins with 365 days (free tier limit)...")
print(f"\n{'Coin':<15} {'Launch':<20} {'Days':<8} {'Data Pts':<10} {'First Date':<12} {'Last Date':<12}")
print("-" * 95)

for coin_id, label in coins_to_test:
    result = test_single_coin(coin_id, days='365')
    results.append(result)
    
    if result.get('success'):
        print(f"{coin_id:<15} {label:<20} {result['days_span']:<8} {result['data_points']:<10} {result['first_date']:<12} {result['last_date']:<12}")
    else:
        print(f"{coin_id:<15} {label:<20} ERROR: {result.get('error', 'Unknown')}")
    
    time.sleep(7)  # Longer delay to avoid rate limits (free tier ~10-30 calls/min)

with open('/tmp/coingecko-marketcap-probe/coin_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: /tmp/coingecko-marketcap-probe/coin_comparison.json")
