#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests",
# ]
# ///

import requests
import json

url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
params = {'vs_currency': 'usd', 'days': '7'}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    
    # Save full response
    with open('/tmp/coingecko-marketcap-probe/sample_response_7days.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Create abbreviated version
    abbreviated = {
        'prices': data['prices'][:5] + ['...'] + data['prices'][-3:],
        'market_caps': data['market_caps'][:5] + ['...'] + data['market_caps'][-3:],
        'total_volumes': data['total_volumes'][:5] + ['...'] + data['total_volumes'][-3:],
        'metadata': {
            'total_price_points': len(data['prices']),
            'total_market_cap_points': len(data['market_caps']),
            'total_volume_points': len(data['total_volumes'])
        }
    }
    
    with open('/tmp/coingecko-marketcap-probe/sample_response_abbreviated.json', 'w') as f:
        json.dump(abbreviated, f, indent=2)
    
    print("Sample responses saved successfully")
    print(f"Market cap data points: {len(data['market_caps'])}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
